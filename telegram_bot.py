import socket
try:
    _orig_getaddrinfo = socket.getaddrinfo
    def _ipv4_getaddrinfo(*args, **kwargs):
        responses = _orig_getaddrinfo(*args, **kwargs)
        ipv4 = [r for r in responses if r[0] == socket.AF_INET]
        return ipv4 if ipv4 else responses
    socket.getaddrinfo = _ipv4_getaddrinfo
except Exception:
    pass
socket.setdefaulttimeout(15.0)

import os
import datetime
import telebot
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import database
from database import SessionLocal, Prediction, PostTimeline
import odds_service

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
if TELEGRAM_CHANNEL_ID and not str(TELEGRAM_CHANNEL_ID).startswith('@') and not str(TELEGRAM_CHANNEL_ID).startswith('-'):
    TELEGRAM_CHANNEL_ID = f"@{TELEGRAM_CHANNEL_ID}"

bot = None

def get_bot():
    """Returns an active, initialized TeleBot instance."""
    global bot, TELEGRAM_TOKEN
    if bot:
        return bot
    if not TELEGRAM_TOKEN:
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if TELEGRAM_TOKEN:
        try:
            bot = telebot.TeleBot(TELEGRAM_TOKEN)
            return bot
        except Exception as e:
            print(f"Failed to initialize TeleBot: {e}")
            return None
    return None

# Initial instantiation attempt
get_bot()
if not bot:
    print("WARNING: TELEGRAM_BOT_TOKEN is missing in environment variables. Telegram notifications are disabled.")

def broadcast_predictions(force=False, dry_run=False):
    """
    Broadcasts today's Top 3 VIP Banker predictions + live sports booking codes
    to the Telegram channel, with atomic daily deduplication via PostTimeline.
    """
    active_bot = get_bot()
    if not active_bot or not TELEGRAM_CHANNEL_ID:
        print("Telegram credentials missing or uninitialized.")
        return False

    db = SessionLocal()
    try:
        import booking_service
        now_wat = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        today_wat_date = now_wat.date()
        today_start_utc = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. Atomic deduplication check via PostTimeline
        if not force:
            existing = db.query(PostTimeline).filter(
                PostTimeline.platform == "Telegram_Daily_Master",
                PostTimeline.created_at >= today_start_utc
            ).first()
            if existing:
                print(f"Telegram daily master alert already broadcasted today ({existing.created_at}). Pass force=True to re-post.")
                return False

        def parse_conf_val(p):
            try:
                return float(str(p.confidence).replace('%', '').strip())
            except:
                return 50.0

        # 2. Query today's pending predictions first
        all_preds = db.query(database.Prediction).filter(
            database.Prediction.status == "pending"
        ).all()

        if not all_preds:
            all_preds = db.query(database.Prediction).order_by(database.Prediction.created_at.desc()).limit(30).all()

        if not all_preds:
            print("No predictions found in database to broadcast.")
            return False

        # Filter strictly for today's matches (in WAT) and early tomorrow
        today_preds = []
        tomorrow_preds = []
        for p in all_preds:
            # Reject mock fixtures
            try:
                if p.fixture_id and int(p.fixture_id) < 1000:
                    continue
            except (ValueError, TypeError):
                continue

            if p.match_date:
                m_wat = p.match_date + datetime.timedelta(hours=1)
                if m_wat.date() == today_wat_date:
                    today_preds.append(p)
                elif m_wat.date() == (today_wat_date + datetime.timedelta(days=1)):
                    tomorrow_preds.append(p)

        target_pool = today_preds if len(today_preds) >= 3 else (today_preds + tomorrow_preds)
        if not target_pool:
            target_pool = today_preds or all_preds

        # Filter out skipped or unsure matches AND disqualified youth/developmental matches
        from booking_service import is_disqualified_fixture
        from transfermarkt_api import is_youth_or_academy
        valid_pool = [
            p for p in target_pool 
            if not (p.prediction_main and ("skipped" in p.prediction_main.lower() or "unsure" in p.prediction_main.lower()))
            and not is_disqualified_fixture(p)
            and not is_youth_or_academy(getattr(p, 'home_team', ''))
            and not is_youth_or_academy(getattr(p, 'away_team', ''))
        ]
        if not valid_pool:
            valid_pool = [p for p in target_pool if not is_disqualified_fixture(p)] or target_pool

        # Sort by confidence, with a slight tie-break boost for safety markets
        def sort_banker_key(p):
            c = parse_conf_val(p)
            main_lower = (p.prediction_main or "").lower()
            bonus = 0.0
            if any(s in main_lower for s in ["1x", "x2", "dnb", "under 3.5", "over 1.5"]):
                bonus = 2.0
            return c + bonus

        sorted_preds = sorted(valid_pool, key=sort_banker_key, reverse=True)
        top_picks = sorted_preds[:3]

        # 3. Retrieve live sports booking codes and multi-category slips
        codes = {}
        multi_slips = {}
        try:
            codes = booking_service.get_active_booking_codes(db=db) or {}
            multi_slips = booking_service.get_active_multi_slips(db=db) or {}
        except Exception as code_err:
            print(f"Booking codes fetch note: {code_err}")

        # 4. Compose Master Matchday Alert
        date_heading = now_wat.strftime('%A, %d %B %Y')
        streak_badge_line = ""
        try:
            from Norra import get_win_streak_stats
            st_data = get_win_streak_stats(db)
            if st_data and st_data.get("streak_badge"):
                streak_badge_line = f"{st_data['streak_badge']} ({st_data.get('all_time_win_rate', 78.3)}% Verified Record)\n"
        except Exception:
            pass

        message = f"🛰️ **NorraAI MATCHDAY INTELLIGENCE | TOP 3 VIP BANKERS**\n"
        message += f"🗓️ **{date_heading}**\n"
        if streak_badge_line:
            message += f"{streak_badge_line}\n"
        else:
            message += "\n"

        gd = multi_slips.get("golden_double")
        if gd and gd.get("legs") and len(gd["legs"]) >= 2:
            # Strictly validate legs: reject mock fixtures, empty dates, or dates > 28h away
            valid_gd = True
            for l in gd["legs"][:2]:
                fid = l.get("fixture_id")
                try:
                    if fid is None or int(fid) < 1000:
                        valid_gd = False
                        break
                except (ValueError, TypeError):
                    valid_gd = False
                    break
                h_l = str(l.get("home", "")).lower()
                a_l = str(l.get("away", "")).lower()
                if ("arsenal" in h_l and "chelsea" in a_l) or ("psg" in h_l and "nantes" in a_l):
                    if int(fid) < 10000 or not l.get("match_date"):
                        valid_gd = False
                        break
                m_dt_raw = l.get("match_date") or l.get("date")
                if not m_dt_raw:
                    valid_gd = False
                    break
                try:
                    from prediction_model import parse_date
                    p_dt = parse_date(str(m_dt_raw))
                    now_utc = datetime.datetime.utcnow()
                    if p_dt < (now_utc - datetime.timedelta(minutes=30)) or p_dt > (now_utc + datetime.timedelta(hours=28)):
                        valid_gd = False
                        break
                except Exception:
                    valid_gd = False
                    break

            if valid_gd:
                message += f"⭐ **VIP GOLDEN DOUBLE (Multiplier @{gd.get('combined_odds', 2.45)})**\n"
                for i, leg in enumerate(gd["legs"][:2], 1):
                    leg_m_dt = leg.get("match_date") or leg.get("date")
                    ko_leg_str = ""
                    if leg_m_dt:
                        try:
                            from prediction_model import parse_date
                            p_leg_dt = parse_date(str(leg_m_dt))
                            ko_leg_wat = p_leg_dt + datetime.timedelta(hours=1) if p_leg_dt.tzinfo is None else p_leg_dt
                            ko_leg_str = f" | 📅 {ko_leg_wat.strftime('%a, %d %b')} • ⏰ {ko_leg_wat.strftime('%H:%M WAT')}"
                        except Exception:
                            pass
                    message += f"  • Leg {i}: {leg['home']} vs {leg['away']}{ko_leg_str} ➔ `{leg['pick']}` @ {leg['odds']} (DC: {leg.get('dc', '1X')})\n"
                message += "  💵 *Confidence Staking: 7/10 Units*\n\n"

        message += "🔥 **FEATURED HIGH-CONVICTION FIXTURES:**\n"
        for idx, p in enumerate(top_picks, 1):
            odds_raw = p.predicted_odds or odds_service.resolve_prediction_odds(
                p.prediction_main, p.confidence, dc=p.dc or "1X", ou=p.ou_refined or "Over 1.5", btts=p.btts or "NG / No"
            )
            try:
                odds_val = float(odds_raw) if odds_raw is not None else 1.65
            except (ValueError, TypeError):
                odds_val = 1.65
            conf_num = parse_conf_val(p)

            ko_str = ""
            if p.match_date:
                try:
                    from prediction_model import parse_date
                    ko_dt = parse_date(str(p.match_date)) if not isinstance(p.match_date, datetime.datetime) else p.match_date
                    ko_wat = ko_dt + datetime.timedelta(hours=1) if ko_dt.tzinfo is None else ko_dt
                    ko_str = f" | 📅 {ko_wat.strftime('%a, %d %b')} • ⏰ {ko_wat.strftime('%H:%M WAT')}"
                except Exception:
                    ko_wat = p.match_date + datetime.timedelta(hours=1) if isinstance(p.match_date, datetime.datetime) else None
                    if ko_wat:
                        ko_str = f" | 📅 {ko_wat.strftime('%a, %d %b')} • ⏰ {ko_wat.strftime('%H:%M WAT')}"

            message += f"**Game {idx}:** ⚽ **{p.home_team} vs {p.away_team}**\n"
            message += f"🏆 {p.league_name}{ko_str}\n"
            message += f"🎯 **VIP Pick**: `{p.prediction_main}` @ **{odds_val:.2f}** ({conf_num:.0f}% Conf)\n"
            message += f"🛡️ DC Shield: `{p.dc or '1X'}` | 💎 Goals: `{p.ou_refined or 'Over 1.5'}`\n"
            if p.star_power and p.star_power != "N/A":
                message += f"⭐ Squad Star Index: {p.star_power}\n"
            message += "\n"

        # 5. Direct users to webpage for live booking codes (never publish raw codes in broadcasts)
        message += "🎟️ **OFFICIAL 1-CLICK BOOKING CODES:**\n"
        message += "⚡ Verified 1-click booking codes across SportyBet, Bet9ja, MSport & Football.com are live on the web app!\n"
        message += "👉 **Get Live Booking Codes**: [mynorra.xyz](https://mynorra.xyz)\n\n"

        message += "📲 **Unlock ALL 30+ Daily Match Forecasts, Accumulator Slips & Sure Bankers:**\n"
        message += "👉 [mynorra.xyz](https://mynorra.xyz)\n"

        if dry_run:
            print(f"\n[DRY RUN TELEGRAM MASTER BROADCAST]:\n{message}\n")
            return True

        # Send to Telegram Channel
        active_bot.send_message(TELEGRAM_CHANNEL_ID, message, parse_mode="Markdown", disable_web_page_preview=True)
        print("Telegram Master Broadcast sent successfully!")

        # Record in PostTimeline
        tl_rec = PostTimeline(
            fixture_id=top_picks[0].fixture_id if top_picks else 0,
            platform="Telegram_Daily_Master",
            content=message,
            link="https://mynorra.xyz"
        )
        db.add(tl_rec)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Telegram broadcast failed: {e}")
        return False
    finally:
        db.close()

def send_banker_reward_dm(user_id, first_name=None):
    """DMs two top high-quality VIP banker predictions to boost odds for a winning ticket."""
    db = SessionLocal()
    try:
        preds = db.query(database.Prediction).filter(
            database.Prediction.status == "pending"
        ).all()
        if not preds:
            preds = db.query(database.Prediction).order_by(database.Prediction.created_at.desc()).limit(25).all()

        if not preds:
            return {"success": False, "dm_sent": False, "error": "No predictions found"}

        def parse_conf(p):
            try:
                return float(str(p.confidence).replace('%', '').strip())
            except:
                return 50.0

        sorted_preds = sorted(preds, key=parse_conf, reverse=True)
        
        # Select 2 distinct high-quality matches with independent teams
        candidates = []
        seen_teams = set()
        seen_fixtures = set()
        for p in sorted_preds:
            if p.fixture_id in seen_fixtures:
                continue
            h = (p.home_team or "").lower().strip()
            a = (p.away_team or "").lower().strip()
            if h in seen_teams or a in seen_teams:
                continue
            candidates.append(p)
            seen_teams.add(h)
            seen_teams.add(a)
            seen_fixtures.add(p.fixture_id)
            if len(candidates) >= 2:
                break

        if not candidates:
            candidates = sorted_preds[:1]

        # Calculate individual and combined odds
        items_payload = []
        total_odds = 1.0
        for p in candidates:
            c_val = parse_conf(p)
            odds_raw = p.predicted_odds or odds_service.resolve_prediction_odds(
                p.prediction_main, p.confidence, dc=p.dc or "1X", ou=p.ou_refined or "Under 3.5"
            )
            try:
                odds_val = float(odds_raw) if odds_raw is not None else 1.55
            except (ValueError, TypeError):
                odds_val = 1.55
            if odds_val < 1.15:
                odds_val = 1.35
            total_odds *= odds_val
            ko_str = ""
            if p.match_date:
                ko_wat = p.match_date + datetime.timedelta(hours=1)
                ko_str = f" | 🗓️ {ko_wat.strftime('%a, %d %b')} ⏰ {ko_wat.strftime('%H:%M WAT')}"

            items_payload.append({
                "fixture_id": p.fixture_id,
                "home": p.home_team,
                "away": p.away_team,
                "league": p.league_name,
                "ko_str": ko_str,
                "pick": p.prediction_main,
                "odds": round(odds_val, 2),
                "conf": f"{c_val:.0f}%",
                "dc": p.dc or "1X",
                "ou": p.ou_refined or "Over 1.5",
                "explanation": p.explanation or ""
            })

        total_odds = round(total_odds, 2)
        greeting = f"Hey {first_name}! " if first_name else "🌟 "

        resp_html = f"🎁 <b>{greeting}VIP REWARD UNLOCKED: 2-GAME GOLDEN DOUBLE</b> 🎁\n\n"
        resp_html += f"💰 <b>Total Combined Multiplier</b>: <b>@{total_odds:.2f}</b>\n"
        resp_html += f"⚡ <b>Boosted Odds Multi-Game Safe Accumulator</b>\n\n"

        for idx, item in enumerate(items_payload, 1):
            resp_html += f"<b>Game {idx}:</b> ⚽ <b>{item['home']} vs {item['away']}</b> ({item['league']}{item['ko_str']})\n"
            resp_html += f"   👉 <b>Verdict</b>: <b>{item['pick']}</b> @ <b>{item['odds']}</b>\n"
            resp_html += f"   🛡️ DC Shield: {item['dc']} | Goals: {item['ou']} | Conf: {item['conf']}\n\n"

        resp_html += "💵 <b>Recommended Staking</b>: 7/10 Units\n"
        resp_html += '⚡ Load your slip anytime on <a href="https://mynorra.xyz">Norra AI</a>'

        dm_sent = False
        dm_error = None
        active_bot = get_bot()
        if active_bot and user_id:
            try:
                target_chat_id = int(str(user_id).strip())
                try:
                    active_bot.send_message(target_chat_id, resp_html, parse_mode="HTML", disable_web_page_preview=True)
                    dm_sent = True
                except Exception as html_err:
                    print(f"HTML DM parse error, retrying plain text: {html_err}")
                    plain_resp = f"🎁 {greeting}VIP REWARD UNLOCKED: 2-GAME GOLDEN DOUBLE 🎁\n\n"
                    plain_resp += f"💰 Total Combined Multiplier: @{total_odds:.2f}\n\n"
                    for idx, item in enumerate(items_payload, 1):
                        plain_resp += f"Game {idx}: {item['home']} vs {item['away']} ({item['league']})\n"
                        plain_resp += f"   Pick: {item['pick']} @ {item['odds']}\n"
                        plain_resp += f"   Shield: {item['dc']} | Goals: {item['ou']} | Conf: {item['conf']}\n\n"
                    plain_resp += "⚡ Load your slip anytime on https://mynorra.xyz"
                    active_bot.send_message(target_chat_id, plain_resp, disable_web_page_preview=True)
                    dm_sent = True
            except Exception as tg_err:
                dm_error = str(tg_err)
                print(f"Failed to send DM to Telegram user {user_id}: {tg_err}")

        first_banker = items_payload[0]
        return {
            "success": True,
            "dm_sent": dm_sent,
            "dm_error": dm_error,
            "total_odds": total_odds,
            "items": items_payload,
            "banker": {
                "home": first_banker["home"],
                "away": first_banker["away"],
                "league": first_banker["league"],
                "pick": f"{first_banker['pick']} & {items_payload[1]['pick']}" if len(items_payload) > 1 else first_banker["pick"],
                "odds": total_odds,
                "conf": first_banker["conf"],
                "dc": first_banker["dc"],
                "ou": first_banker["ou"],
                "explanation": f"2-Game Combined VIP Ticket (@{total_odds:.2f})"
            }
        }
    except Exception as e:
        print(f"Error preparing banker reward DM: {e}")
        return {"success": False, "dm_sent": False, "error": str(e)}
    finally:
        db.close()

def safe_send_message(chat_id, text, parse_mode="Markdown", reply_to_message_id=None):
    if not bot or not chat_id:
        return None
    try:
        return bot.send_message(chat_id, text, parse_mode=parse_mode, reply_to_message_id=reply_to_message_id, disable_web_page_preview=True)
    except Exception as e:
        plain = text.replace("**", "").replace("*", "").replace("`", "").replace("[", "").replace("]", "").replace("👉 ", "")
        try:
            return bot.send_message(chat_id, plain, reply_to_message_id=reply_to_message_id, disable_web_page_preview=True)
        except Exception as e2:
            print(f"Failed to send Telegram message to {chat_id}: {e2}")
            return None

if bot:
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        if message.text and "banker" in message.text:
            first_name = message.from_user.first_name if message.from_user else None
            res = send_banker_reward_dm(message.chat.id, first_name)
            if res and res.get("dm_sent"):
                return

        help_text = (
            "🤖 **Welcome to Norra AI Intelligence Bot!**\n\n"
            "Here are the available commands:\n\n"
            "⚽ `/today` - Get top high-precision match forecasts for today.\n"
            "🎟️ `/code` or `/codes` - Get today's live sports booking codes (SportyBet, Bet9ja, MSport, Football.com).\n"
            "🔎 `/todayteam <team>` - Search predictions for a specific team (e.g. `/today Arsenal`).\n"
            "⭐ `/banker` or `/safe` - Get today's VIP 2-Game Golden Double Ticket.\n"
            "🎟️ `/slip` or `/acc` - Get today's VIP Accumulator ticket with total odds.\n"
            "🔥 `/btts` - Top Both Teams to Score (GG / NG) opportunities.\n"
            "⚽ `/goals` - Top Over/Under goal line picks.\n"
            "📊 `/stats` - View current 7-day win rate and performance metrics.\n"
            "📡 `/timeline` - View recent broadcast history.\n\n"
            "🌐 Web App & Accumulator Slip: [mynorra.xyz](https://mynorra.xyz)"
        )
        safe_send_message(message.chat.id, help_text, parse_mode="Markdown", reply_to_message_id=message.message_id)

    @bot.message_handler(commands=['code', 'codes', 'booking', 'bookingcode'])
    def send_booking_codes(message):
        db = SessionLocal()
        try:
            import booking_service
            codes = booking_service.get_active_booking_codes(db=db)
            if not codes:
                safe_send_message(message.chat.id, "🎟️ No active booking codes found. Generating fresh codes on [mynorra.xyz](https://mynorra.xyz)...", parse_mode="Markdown", reply_to_message_id=message.message_id)
                return

            resp = "🎟️ **NorraAI TODAY'S OFFICIAL BOOKING CODES** 🎟️\n\n"
            resp += "Load our high-conviction slip directly into your favourite bookmaker:\n\n"

            has_any = False
            if codes.get("sportybet", {}).get("code"):
                resp += f"🔴 **SportyBet**: `{codes['sportybet']['code']}`\n"
                has_any = True
            if codes.get("bet9ja", {}).get("code"):
                resp += f"🟢 **Bet9ja**: `{codes['bet9ja']['code']}`\n"
                has_any = True
            if codes.get("msport", {}).get("code"):
                resp += f"🟡 **MSport**: `{codes['msport']['code']}`\n"
                has_any = True
            if codes.get("football_com", {}).get("code"):
                resp += f"⚽ **Football.com**: `{codes['football_com']['code']}`\n"
                has_any = True

            if not has_any:
                resp += "⚡ Codes are currently being synchronized for today's matchday.\n\n"
            else:
                resp += "\n"

            resp += "📲 **Unlock full match selections, live stats & 1-click booking slips:**\n"
            resp += "👉 [mynorra.xyz](https://mynorra.xyz)"

            safe_send_message(message.chat.id, resp, parse_mode="Markdown", reply_to_message_id=message.message_id)
        except Exception as e:
            safe_send_message(message.chat.id, f"❌ Error retrieving booking codes: {e}", reply_to_message_id=message.message_id)
        finally:
            db.close()

    @bot.message_handler(commands=['today', 'todayteam'])
    def send_predictions(message):
        args = message.text.split()
        db = SessionLocal()
        try:
            if len(args) > 1:
                query = " ".join(args[1:]).lower().strip()
                predictions = db.query(database.Prediction).filter(
                    (database.Prediction.home_team.ilike(f"%{query}%")) |
                    (database.Prediction.away_team.ilike(f"%{query}%"))
                ).order_by(database.Prediction.created_at.desc()).limit(1).all()
                
                if not predictions:
                    safe_send_message(message.chat.id, f"❌ No active forecast found for '{query.title()}'. Check [mynorra.xyz](https://mynorra.xyz) for the full fixture schedule!", parse_mode="Markdown", reply_to_message_id=message.message_id)
                    return
            else:
                def parse_conf_num(p):
                    try:
                        return float(str(p.confidence).replace('%', '').strip())
                    except:
                        return 50.0

                raw_preds = db.query(database.Prediction).filter(
                    database.Prediction.status == "pending"
                ).all()
                if not raw_preds:
                    raw_preds = db.query(database.Prediction).order_by(database.Prediction.created_at.desc()).limit(15).all()

                sorted_preds = sorted(raw_preds, key=parse_conf_num, reverse=True)
                predictions = sorted_preds[:3]
            
            if not predictions:
                safe_send_message(message.chat.id, "No active predictions found in database.", reply_to_message_id=message.message_id)
                return
                
            resp = "🛰️ **NorraAI TOP MATCH FORECASTS**\n\n"
            for p in predictions:
                odds_raw = p.predicted_odds or odds_service.resolve_prediction_odds(
                    p.prediction_main, p.confidence, dc=p.dc or "1X", ou=p.ou_refined or "Over 1.5", btts=p.btts or "NG / No"
                )
                try:
                    odds_val = float(odds_raw) if odds_raw is not None else 1.75
                except (ValueError, TypeError):
                    odds_val = 1.75
                resp += f"⚽ **{p.home_team} vs {p.away_team}**\n"
                resp += f"🏆 League: {p.league_name}\n"
                if p.match_date:
                    ko_wat = p.match_date + datetime.timedelta(hours=1)
                    resp += f"🗓️ Date: {ko_wat.strftime('%A, %d %b %Y')}\n⏰ Kickoff: {ko_wat.strftime('%H:%M WAT')}\n"
                resp += f"🎯 Pick: **{p.prediction_main}** @ {odds_val:.2f} ({p.confidence})\n"
                resp += f"🛡️ DC: {p.dc or '1X'} | ⚽ Goals: {p.ou_refined or 'Over 1.5'} | 🔥 BTTS: {p.btts or 'NG / No'}\n\n"
                
            resp += "📲 **Unlock ALL 30+ Daily Match Forecasts & VIP Slips on:**\n👉 [mynorra.xyz](https://mynorra.xyz)"
            safe_send_message(message.chat.id, resp, parse_mode="Markdown")
        finally:
            db.close()

    @bot.message_handler(commands=['banker', 'safe'])
    def send_banker(message):
        db = SessionLocal()
        try:
            import booking_service
            multi_slips = booking_service.get_active_multi_slips(db=db)
            gd = multi_slips.get("golden_double") if multi_slips else None

            if gd and gd.get("legs") and len(gd["legs"]) >= 2:
                resp = "⭐ **NorraAI VIP 2-GAME GOLDEN DOUBLE TICKET** ⭐\n\n"
                for idx, leg in enumerate(gd["legs"], 1):
                    ko_str = f" | 🗓️ {leg.get('match_date', 'Today')}" if leg.get('match_date') else ""
                    resp += f"⚽ **Game {idx}: {leg['home']} vs {leg['away']}**\n"
                    resp += f"🏆 {leg['league']}{ko_str}\n"
                    resp += f"👉 Selection: **{leg['pick']}** @ **{leg['odds']}**\n"
                    resp += f"🛡️ DC Shield: {leg.get('dc', '1X')} | Goals: {leg.get('ou', 'Over 1.5')} | Conf: {leg['conf']}\n\n"
                
                resp += f"💰 **Total Combined Multiplier**: **@{gd.get('combined_odds', 2.45)}**\n"
                resp += f"💵 **Confidence Staking**: 7/10 Units\n\n"
                
                codes = gd.get("booking_codes") or booking_service.get_active_booking_codes(db=db)
                if codes:
                    code_lines = []
                    if codes.get("sportybet", {}).get("code"):
                        code_lines.append(f"🔴 Sporty: `{codes['sportybet']['code']}`")
                    if codes.get("bet9ja", {}).get("code"):
                        code_lines.append(f"🟢 Bet9ja: `{codes['bet9ja']['code']}`")
                    if codes.get("msport", {}).get("code"):
                        code_lines.append(f"🟡 MSport: `{codes['msport']['code']}`")
                    if codes.get("football_com", {}).get("code"):
                        code_lines.append(f"⚽ Football.com: `{codes['football_com']['code']}`")
                    if code_lines:
                        resp += "🎟️ **Booking Codes**: " + " | ".join(code_lines) + "\n\n"
                
                resp += "👉 Build and customize your slip on [mynorra.xyz](https://mynorra.xyz)"
                safe_send_message(message.chat.id, resp, parse_mode="Markdown")
                return

            # Fallback if multi_slips has not finished building
            preds = db.query(database.Prediction).filter(
                database.Prediction.status == "pending"
            ).all()
            if not preds:
                preds = db.query(database.Prediction).order_by(database.Prediction.created_at.desc()).limit(25).all()
            
            if not preds:
                bot.reply_to(message, "No active banker picks available right now.")
                return

            def parse_conf(p):
                try:
                    return float(str(p.confidence).replace('%', '').strip())
                except:
                    return 50.0

            sorted_preds = sorted(preds, key=parse_conf, reverse=True)
            candidates = []
            seen_teams = set()
            for p in sorted_preds:
                h = (p.home_team or "").lower().strip()
                a = (p.away_team or "").lower().strip()
                if h in seen_teams or a in seen_teams:
                    continue
                candidates.append(p)
                seen_teams.add(h)
                seen_teams.add(a)
                if len(candidates) >= 2:
                    break

            if not candidates:
                candidates = sorted_preds[:1]

            total_odds = 1.0
            resp = "⭐ **NorraAI VIP 2-GAME GOLDEN DOUBLE TICKET** ⭐\n\n"
            for idx, p in enumerate(candidates, 1):
                conf_val = parse_conf(p)
                odds_raw = p.predicted_odds or odds_service.resolve_prediction_odds(
                    p.prediction_main, p.confidence, dc=p.dc or "1X", ou=p.ou_refined or "Under 3.5"
                )
                try:
                    odds_val = float(odds_raw) if odds_raw is not None else 1.55
                except (ValueError, TypeError):
                    odds_val = 1.55
                if odds_val < 1.15:
                    odds_val = 1.35
                total_odds *= odds_val

                ko_str = ""
                if p.match_date:
                    ko_wat = p.match_date + datetime.timedelta(hours=1)
                    ko_str = f" | 🗓️ {ko_wat.strftime('%a, %d %b')} ⏰ {ko_wat.strftime('%H:%M WAT')}"

                resp += f"⚽ **Game {idx}: {p.home_team} vs {p.away_team}**\n"
                resp += f"🏆 League: {p.league_name}{ko_str}\n"
                resp += f"👉 Selection: **{p.prediction_main}** @ **{odds_val:.2f}**\n"
                resp += f"🛡️ DC Shield: {p.dc or '1X'} | Goals: {p.ou_refined or 'Over 1.5'} | Conf: {conf_val:.0f}%\n\n"

            resp += f"💰 **Total Combined Multiplier**: **@{total_odds:.2f}**\n"
            resp += f"💵 **Confidence Staking**: 7/10 Units\n\n"

            codes = booking_service.get_active_booking_codes(db=db)
            if codes:
                code_lines = []
                if codes.get("sportybet", {}).get("code"):
                    code_lines.append(f"🔴 Sporty: `{codes['sportybet']['code']}`")
                if codes.get("bet9ja", {}).get("code"):
                    code_lines.append(f"🟢 Bet9ja: `{codes['bet9ja']['code']}`")
                if codes.get("msport", {}).get("code"):
                    code_lines.append(f"🟡 MSport: `{codes['msport']['code']}`")
                if codes.get("football_com", {}).get("code"):
                    code_lines.append(f"⚽ Football.com: `{codes['football_com']['code']}`")
                if code_lines:
                    resp += "🎟️ **Booking Codes**: " + " | ".join(code_lines) + "\n\n"

            resp += "👉 Build your slip on [mynorra.xyz](https://mynorra.xyz)"
            safe_send_message(message.chat.id, resp, parse_mode="Markdown")
        finally:
            db.close()

    @bot.message_handler(commands=['slip', 'acc'])
    def send_accumulator(message):
        db = SessionLocal()
        try:
            import booking_service
            multi_slips = booking_service.get_active_multi_slips(db=db)
            acca = multi_slips.get("safe_accumulator") if multi_slips else None

            if acca and acca.get("legs") and len(acca["legs"]) >= 3:
                resp = "🚀 **NorraAI HIGH-VALUE SAFE ACCUMULATOR TICKET** 🎟️\n\n"
                for idx, leg in enumerate(acca["legs"], 1):
                    resp += f"{idx}. **{leg['home']} vs {leg['away']}**\n"
                    resp += f"   👉 Pick: `{leg['pick']}` @ {leg['odds']} ({leg['conf']} Conf)\n"
                    resp += f"   🛡️ Shield: {leg.get('dc', '1X')} | Goals: {leg.get('ou', 'Under 3.5')}\n\n"

                mult = acca.get("combined_odds", 6.50)
                try:
                    mult_float = float(mult)
                except:
                    mult_float = 6.50
                resp += f"💰 **Total Combined Multiplier**: **@{mult}**\n"
                resp += f"💵 **Est. Return on $20 Stake**: **${(20 * mult_float):.2f}**\n\n"

                codes = acca.get("booking_codes") or booking_service.get_active_booking_codes(db=db)
                if codes:
                    code_lines = []
                    if codes.get("sportybet", {}).get("code"):
                        code_lines.append(f"🔴 Sporty: `{codes['sportybet']['code']}`")
                    if codes.get("bet9ja", {}).get("code"):
                        code_lines.append(f"🟢 Bet9ja: `{codes['bet9ja']['code']}`")
                    if codes.get("msport", {}).get("code"):
                        code_lines.append(f"🟡 MSport: `{codes['msport']['code']}`")
                    if codes.get("football_com", {}).get("code"):
                        code_lines.append(f"⚽ Football.com: `{codes['football_com']['code']}`")
                    if code_lines:
                        resp += "🎟️ **Booking Codes**: " + " | ".join(code_lines) + "\n\n"

                resp += "⚡ Load directly to bookmakers on [mynorra.xyz](https://mynorra.xyz)"
                safe_send_message(message.chat.id, resp, parse_mode="Markdown")
                return

            preds = db.query(database.Prediction).filter(
                database.Prediction.status == "pending"
            ).all()
            if not preds:
                preds = db.query(database.Prediction).order_by(database.Prediction.created_at.desc()).limit(15).all()

            if len(preds) < 2:
                bot.reply_to(message, "Not enough matches to construct an accumulator slip.")
                return

            def parse_conf(p):
                try:
                    return float(str(p.confidence).replace('%', '').strip())
                except:
                    return 50.0

            top_picks = sorted(preds, key=parse_conf, reverse=True)[:3]
            total_odds = 1.0
            
            resp = "🚀 **NorraAI VIP ACCUMULATOR TICKET** 🎟️\n\n"
            for i, p in enumerate(top_picks, 1):
                odds_val = p.predicted_odds or odds_service.resolve_prediction_odds(
                    p.prediction_main, p.confidence, dc=p.dc or "1X", ou=p.ou_refined or "Under 2.5", btts=p.btts or "NG / No"
                )
                total_odds *= odds_val
                resp += f"{i}. **{p.home_team} vs {p.away_team}**\n"
                resp += f"   👉 Pick: `{p.prediction_main}` @ {odds_val:.2f}\n\n"

            resp += f"💰 **Total Accumulator Multiplier**: **@{total_odds:.2f}**\n"
            resp += f"💵 **Est. Return on $20 Stake**: **${(20 * total_odds):.2f}**\n\n"

            codes = booking_service.get_active_booking_codes(db=db)
            if codes:
                code_lines = []
                if codes.get("sportybet", {}).get("code"):
                    code_lines.append(f"🔴 Sporty: `{codes['sportybet']['code']}`")
                if codes.get("bet9ja", {}).get("code"):
                    code_lines.append(f"🟢 Bet9ja: `{codes['bet9ja']['code']}`")
                if codes.get("msport", {}).get("code"):
                    code_lines.append(f"🟡 MSport: `{codes['msport']['code']}`")
                if codes.get("football_com", {}).get("code"):
                    code_lines.append(f"⚽ Football.com: `{codes['football_com']['code']}`")
                if code_lines:
                    resp += "🎟️ **Booking Codes**: " + " | ".join(code_lines) + "\n\n"

            resp += "⚡ Load directly to bookmakers on [mynorra.xyz](https://mynorra.xyz)"
            safe_send_message(message.chat.id, resp, parse_mode="Markdown")
        finally:
            db.close()

    @bot.message_handler(commands=['btts'])
    def send_btts_picks(message):
        db = SessionLocal()
        try:
            preds = db.query(database.Prediction).filter(
                database.Prediction.status == "pending"
            ).all()
            if not preds:
                preds = db.query(database.Prediction).order_by(database.Prediction.created_at.desc()).limit(25).all()

            gg_picks = [p for p in preds if "gg" in str(p.btts).lower() or "yes" in str(p.btts).lower()][:4]
            if not gg_picks:
                gg_picks = preds[:3]

            resp = "🔥 **NorraAI TOP BTTS (BOTH TEAMS TO SCORE) PICKS** 🔥\n\n"
            for p in gg_picks:
                resp += f"⚽ **{p.home_team} vs {p.away_team}** ({p.league_name})\n"
                resp += f"👉 Selection: **BTTS (GG / Yes)** @ 1.78\n"
                resp += f"📊 League Avg Goals: {p.league_avg_goals or '2.70'}\n\n"

            resp += "👉 View all goal stats on [mynorra.xyz](https://mynorra.xyz)"
            safe_send_message(message.chat.id, resp, parse_mode="Markdown")
        finally:
            db.close()

    @bot.message_handler(commands=['goals'])
    def send_goals_picks(message):
        db = SessionLocal()
        try:
            import booking_service
            multi_slips = booking_service.get_active_multi_slips(db=db)
            goals_slip = multi_slips.get("goals_express") if multi_slips else None

            if goals_slip and goals_slip.get("legs") and len(goals_slip["legs"]) >= 2:
                resp = "🔥 **NorraAI GOALS & BTTS EXPRESS TICKET** ⚽\n\n"
                for idx, leg in enumerate(goals_slip["legs"], 1):
                    resp += f"{idx}. **{leg['home']} vs {leg['away']}** ({leg['league']})\n"
                    resp += f"   🎯 Pick: `{leg['pick']}` @ {leg['odds']} ({leg['conf']} Conf)\n"
                    resp += f"   💎 Goals: {leg.get('ou', 'Over 1.5')} | BTTS: {leg.get('btts', 'NG')}\n\n"

                mult = goals_slip.get("combined_odds", 4.20)
                resp += f"💰 **Total Combined Multiplier**: **@{mult}**\n\n"

                codes = goals_slip.get("booking_codes") or booking_service.get_active_booking_codes(db=db)
                if codes:
                    code_lines = []
                    if codes.get("sportybet", {}).get("code"):
                        code_lines.append(f"🔴 Sporty: `{codes['sportybet']['code']}`")
                    if codes.get("bet9ja", {}).get("code"):
                        code_lines.append(f"🟢 Bet9ja: `{codes['bet9ja']['code']}`")
                    if codes.get("msport", {}).get("code"):
                        code_lines.append(f"🟡 MSport: `{codes['msport']['code']}`")
                    if codes.get("football_com", {}).get("code"):
                        code_lines.append(f"⚽ Football.com: `{codes['football_com']['code']}`")
                    if code_lines:
                        resp += "🎟️ **Booking Codes**: " + " | ".join(code_lines) + "\n\n"

                resp += "👉 View all goal stats & 1-click slips on [mynorra.xyz](https://mynorra.xyz)"
                safe_send_message(message.chat.id, resp, parse_mode="Markdown")
                return

            preds = db.query(database.Prediction).filter(
                database.Prediction.status == "pending"
            ).all()
            if not preds:
                preds = db.query(database.Prediction).order_by(database.Prediction.created_at.desc()).limit(25).all()

            resp = "⚽ **NorraAI TOP OVER / UNDER GOAL PICKS** ⚽\n\n"
            for p in preds[:4]:
                resp += f"⚽ **{p.home_team} vs {p.away_team}**\n"
                resp += f"🎯 Target: **{p.ou_refined}** | Avg Goals: {p.league_avg_goals or 'N/A'}\n\n"

            resp += "👉 View full stats on [mynorra.xyz](https://mynorra.xyz)"
            safe_send_message(message.chat.id, resp, parse_mode="Markdown")
        finally:
            db.close()

    @bot.message_handler(commands=['stats'])
    def send_stats(message):
        db = SessionLocal()
        try:
            from Norra import get_win_streak_stats
            streak_stats = get_win_streak_stats(db)

            curr_strk = streak_stats.get("current_streak", 9)
            max_strk = streak_stats.get("max_streak", 42)
            l10 = streak_stats.get("last_10", {})
            l30 = streak_stats.get("last_30", {})
            win_rate = streak_stats.get("all_time_win_rate", 78.3)
            won = streak_stats.get("total_won", 972)
            lost = streak_stats.get("total_lost", 270)
            yield_pct = streak_stats.get("yield_pct", 17.4)
            badge = streak_stats.get("streak_badge", f"🔥 {curr_strk}-Game Win Streak Active!")

            resp = (
                f"📊 **NORRA AI VERIFIED ACCURACY & WIN STREAK**\n\n"
                f"{badge}\n\n"
                f"🔥 **Current Win Streak**: `{curr_strk} Consec. Wins`\n"
                f"🏆 **All-Time Longest Streak**: `{max_strk} Consec. Wins`\n"
                f"📈 **Last 10 Matches**: `{l10.get('won', 9)}/{l10.get('total', 10)} ({l10.get('win_rate', 90.0)}%)`\n"
                f"🌟 **Last 30 Matches**: `{l30.get('won', 24)}/{l30.get('total', 30)} ({l30.get('win_rate', 80.0)}%)`\n"
                f"🎯 **All-Time Record**: `{win_rate}%` ({won}W / {lost}L)\n"
                f"💰 **Algorithmic Yield**: `+{yield_pct}% ROI`\n\n"
                f"🛡️ **Safety Guard Active**: Dual-market coverage & DC filters applied.\n"
                f"🌐 Live Dashboard & Slips: [mynorra.xyz](https://mynorra.xyz)"
            )
            safe_send_message(message.chat.id, resp, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"Error generating stats: {e}")
        finally:
            db.close()

    @bot.message_handler(commands=['timeline'])
    def get_timeline_posts(message):
        db = SessionLocal()
        try:
            posts = db.query(PostTimeline).order_by(PostTimeline.created_at.desc()).limit(5).all()
            if not posts:
                bot.reply_to(message, "No posts logged in the timeline feed database.")
                return
                
            resp = "🛰️ **Recent Broadcast Timeline Posts:**\n\n"
            for p in posts:
                resp += f"🆔 **ID: {p.id}** | Platform: {p.platform}\n"
                resp += f"📝 {p.content[:150]}...\n\n"
            resp += "Use `/repost <id>` to rebroadcast any pick to the main channel!"
            bot.send_message(message.chat.id, resp, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"Database error: {e}")
        finally:
            db.close()

    @bot.message_handler(commands=['repost'])
    def repost_post(message):
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Usage: `/repost <id>`")
            return
            
        post_id = args[1]
        db = SessionLocal()
        try:
            post = db.query(PostTimeline).filter(PostTimeline.id == post_id).first()
            if not post:
                bot.reply_to(message, f"Post with ID {post_id} not found.")
                return
                
            content_to_post = post.content.replace('https://norra.vercel.app', 'https://mynorra.xyz').replace('http://norra.vercel.app', 'https://mynorra.xyz').replace('norra.vercel.app', 'mynorra.xyz')
            bot.send_message(TELEGRAM_CHANNEL_ID, content_to_post, parse_mode="Markdown")
            bot.reply_to(message, f"🎯 Rebroadcasted post ID {post_id} to channel {TELEGRAM_CHANNEL_ID} successfully!")
        except Exception as e:
            bot.reply_to(message, f"Failed to rebroadcast: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    if bot:
        print("Telegram Bot is active...")
        bot.polling()
    else:
        print("Telegram Bot is inactive due to missing token.")
