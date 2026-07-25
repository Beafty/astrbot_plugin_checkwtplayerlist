import json
import csv
from pathlib import Path
from functools import lru_cache

UNIT_ID_COLUMN = "<ID|readonly|noverify>"
ZH_NAME_COLUMNS = ("<Chinese>", "<TChinese>", "<HChinese>")

def get_id(row: dict) -> str:
    return (row.get(UNIT_ID_COLUMN) or "").strip().strip('"')

def get_zh_name(row: dict) -> str:
    for col in ZH_NAME_COLUMNS:
        value = (row.get(col) or "").strip().strip('"')
        if value:
            return value
    return ""

@lru_cache(maxsize=1)
def load_units_name_map():
    units_name_map = {}
    csv_path = Path(__file__).resolve().parent / "lang" / "units.csv"

    if not csv_path.exists():
        return units_name_map

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            unit_id = get_id(row)
            zh_name = get_zh_name(row)

            if not unit_id or not zh_name:
                continue

            units_name_map[unit_id] = zh_name

            if unit_id.endswith("_shop"):
                units_name_map[unit_id[:-len("_shop")]] = zh_name

    return units_name_map

@lru_cache(maxsize=1)
def load_unit_type():
    unit_type_map = {}
    csv_path = Path(__file__).resolve().parent / "lang" / "menu.csv"
    if not csv_path.exists():
        return unit_type_map
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            unit_type = get_id(row)
            zh_name = get_zh_name(row)
            if not unit_type or not zh_name:
                continue
            unit_type_map[unit_type] = zh_name
            if unit_type.startswith("mainmenu/type_"):
                unit_type_map[unit_type[len("mainmenu/type_"):]] = zh_name
    return unit_type_map

def translate_unit_name(name: str):
    if not name:
        return name
    name = str(name).strip()
    mp = load_units_name_map()

    if name in mp:
        return mp[name]

    return mp.get(name.split("/")[-1], name)

def translate_unit_type(unit_type: str):
    if not unit_type:
        return unit_type
    unit_type = str(unit_type).strip()
    mp = load_unit_type()

    if unit_type in mp:
        return mp[unit_type]

    return mp.get(unit_type.split("/")[-1], unit_type)

def check_room_id(room_id: str):
    if room_id is None:
        return False
    return (
        len(room_id) == 15
        and all(c in "0123456789abcdef" for c in room_id)
    )

def convert_mrank_to_br(mrank: str):
    if mrank is None or mrank == "":
        return "-"
    try:
        mrank_val = int(mrank)
        br_val = (mrank_val / 3) + 1.0
        int_part = int(br_val)
        frac = br_val - int_part
        if frac < 0.2:
            br_suffix = ".0"
        elif frac < 0.5:
            br_suffix = ".3"
        else:
            br_suffix = ".7"
        return f"{int_part}{br_suffix}"
    except (ValueError, TypeError):
        return str(mrank)

def extract_room_payload(result):
    if not isinstance(result, dict):
        return {}, ""
    data = result.get("data")
    if isinstance(data, dict):
        return data, result.get("task", "")
    return result, result.get("task", "")

def get_players(room_data):
    public_players = room_data.get("public", {}) if isinstance(room_data, dict) else {}
    if not isinstance(public_players, dict):
        return []
    players = [
        p for p in public_players.values()
        if isinstance(p, dict) and "id" in p and "name" in p and "team" in p
    ]
    return sorted(
        players,
        key=lambda p: (
            p.get("team", 99),
            p.get("squad", 999999),
            p.get("slot", 999999),
            str(p.get("name", "")).lower(),
        ),
    )

def player_crafts_text(player):
    crafts_info = player.get("crafts_info")
    if isinstance(crafts_info, list) and crafts_info:
        names = []
        for craft in crafts_info:
            if not isinstance(craft, dict):
                continue
            name = translate_unit_name(craft.get("name") or "未知载具")
            ctype = translate_unit_type(craft.get("type") or "")
            rank = craft.get("rank")
            mrank = craft.get("mrank")
            detail = str(name)
            extras = []
            if ctype:
                extras.append(str(ctype))
            if rank not in (None, ""):
                extras.append(f"{rank}级")
            if mrank not in (None, ""):
                extras.append(f"{convert_mrank_to_br(mrank)}")
            if extras:
                detail += f" ({' / '.join(extras)})"
            names.append(detail)
        if names:
            return "".join(f'<div class="craft">{name}</div>' for name in names)

    crafts = player.get("crafts")
    if isinstance(crafts, dict) and crafts:
        return ", ".join(translate_unit_name(str(unit_name)) for craft_id, unit_name in sorted(crafts.items()))
    return "-"

def format_api_result(result):
    room_data, request_task = extract_room_payload(result)
    room_id = room_data.get("roomId") or room_data.get("room_id") or room_data.get("id") or ""
    players = get_players(room_data)
    lines = ["查询成功"]
    if room_id:
        lines.append(f"房间ID: {room_id}")
    if players:
        lines.append(f"玩家数: {len(players)}")
        for player in players:
            clan = player.get("clanTag") or ""
            clan_text = f"[{clan}] " if clan else ""
            lines.append(
                f"T{player.get('team', '-')} {clan_text}{player.get('name', '-')} "
                f"#{player.get('id', '-')} - {player_crafts_text(player)}"
            )
    else:
        return json.dumps(result, ensure_ascii=False)
    return "\n".join(lines)

CLUSTER_NAME_MAP = {
    "SA": "亚服",
    "EU": "欧服",
    "NA": "美服",
    "CIS": "俄服",
}
def format_cluster(cluster):
    return CLUSTER_NAME_MAP.get(cluster, "-") if cluster else "-"

def build_room_render_data(result):
    room_data, request_task = extract_room_payload(result)
    players = get_players(room_data)
    room_id = room_data.get("roomId") or room_data.get("room_id") or room_data.get("id") or "-"
    grouped = {}
    cluster = format_cluster(room_data.get("public", {}).get("cluster"))
    for player in players:
        grouped.setdefault(player.get("team", "-"), []).append(player)

    teams = []
    for team_id, team_players in grouped.items():
        rendered_players = []
        for player in team_players:
            clan = player.get("clanTag") or "无战队"
            country = str(player.get("country") or "-").replace("country_", "")
            raw_br = player.get("mrank") or player.get("rank")
            br_display = convert_mrank_to_br(raw_br)
            rendered_players.append({
                "id": player.get("id", "-"),
                "name": player.get("name") or "-",
                "clan": clan,
                "crafts": player_crafts_text(player),
                "country": country,
                "platform": player.get("platform") or "-",
                "squad": player.get("squad") or "-",
                "tier": player.get("tier") or "-",
                "BR": br_display,
            })
        teams.append({"id": team_id, "players": rendered_players})

    return {
        "room_id": room_id,
        "player_count": len(players),
        "teams": teams,
        "cluster": cluster,
    }


def check_replay_id(replay_id: str):
    if replay_id is None:
        return False
    replay_id = str(replay_id).strip().lower()
    if not replay_id:
        return False
    if replay_id.startswith("0x"):
        replay_id = replay_id[2:]
    if all(c in "0123456789abcdef" for c in replay_id):
        return len(replay_id) <= 16
    return replay_id.isdigit()


def format_replay_time(seconds):
    if seconds is None:
        return "-"
    try:
        s = float(seconds)
        m = int(s) // 60
        sec = int(s) % 60
        return f"{m:02d}:{sec:02d}"
    except (ValueError, TypeError):
        return str(seconds)


SQUAD_COLORS = [
    "#E8F5E9", "#E3F2FD", "#FFF3E0", "#F3E5F5", "#E0F7FA",
    "#FFF9C4", "#F1F8E9", "#FCE4EC", "#EDE7F6", "#EFEBE9",
    "#E8EAF6", "#FFF8E1", "#E0F2F1", "#FBE9E7", "#F1F8E9",
]


def _assign_squad_colors(scores):
    squad_color_map = {}
    color_idx = 0
    for s in scores:
        if s.get("autoSquad", True):
            continue
        sid = s.get("squadId", -1)
        if sid == -1 or sid is None:
            continue
        if sid not in squad_color_map:
            squad_color_map[sid] = SQUAD_COLORS[color_idx % len(SQUAD_COLORS)]
            color_idx += 1
    return squad_color_map


def _assign_squad_groups(scores):
    squad_group_map = {}
    group_idx = 1
    for s in scores:
        if s.get("autoSquad", True):
            continue
        sid = s.get("squadId", -1)
        if sid == -1 or sid is None:
            continue
        if sid not in squad_group_map:
            squad_group_map[sid] = group_idx
            group_idx += 1
    return squad_group_map


SCORE_COLUMN_ORDER = [
    ("autoSquad",        "预组队"),
    ("_name",            "玩家"),
    ("score",            "得分"),
    ("kills",            "空军"),
    ("groundKills",      "地面"),
    ("assists",          "助攻"),
    ("aiKills",          "AI"),
    ("captureZone",      "占点"),
    ("deaths",           "死亡"),
    ("missileEvades",    "规避导弹"),
]
VISIBLE_KEYS = {k for k, _ in SCORE_COLUMN_ORDER}


def _compute_hidden_cols(scores):
    if not scores:
        return set()
    all_numeric = [
        "kills", "deaths", "assists", "score",
        "groundKills", "captureZone", "damageZone",
        "humanKills", "teamKills", "aiKills", "navalKills",
        "missionKills", "missileEvades", "shellInterceptions", "awardDamage",
    ]
    hidden = set()
    for field in all_numeric:
        if field not in VISIBLE_KEYS:
            hidden.add(field)
        elif all(s.get(field, 0) == 0 for s in scores):
            hidden.add(field)
    if all(s.get("autoSquad", False) for s in scores):
        hidden.add("autoSquad")
    return hidden


def _build_team_columns(team_id):
    order = list(SCORE_COLUMN_ORDER)
    if str(team_id) == "1":
        order = list(reversed(order))
    return [{"key": k, "label": l} for k, l in order]


def build_replay_render_data(result):
    data = result.get("data", {}) if isinstance(result, dict) else {}
    scores = data.get("scores", []) or []
    events = data.get("events", []) or []
    vehicles = data.get("vehicles", []) or []

    kill_events = [e for e in events if isinstance(e, dict) and e.get("type") == "kill"]
    kill_events.sort(key=lambda e: e.get("t", 0))

    squad_color_map = _assign_squad_colors(scores)
    squad_group_map = _assign_squad_groups(scores)

    grouped = {}
    for s in scores:
        if not isinstance(s, dict):
            continue
        grouped.setdefault(s.get("team", "-"), []).append(s)

    scores_teams = []
    for team_id in sorted(grouped.keys(), key=lambda t: (str(t).isdigit(), str(t))):
        team_scores = grouped[team_id]
        team_scores.sort(key=lambda s: s.get("score", 0), reverse=True)
        rendered = []
        for i, s in enumerate(team_scores):
            sid = s.get("squadId", -1)
            rendered.append({
                "rank": i + 1,
                "name": s.get("name", "-"),
                "kills": s.get("kills", 0),
                "deaths": s.get("deaths", 0),
                "assists": s.get("assists", 0),
                "score": s.get("score", 0),
                "groundKills": s.get("groundKills", 0),
                "captureZone": s.get("captureZone", 0),
                "damageZone": s.get("damageZone", 0),
                "humanKills": s.get("humanKills", 0),
                "teamKills": s.get("teamKills", 0),
                "aiKills": s.get("aiKills", 0),
                "navalKills": s.get("navalKills", 0),
                "missionKills": s.get("missionKills", 0),
                "missileEvades": s.get("missileEvades", 0),
                "shellInterceptions": s.get("shellInterceptions", 0),
                "awardDamage": s.get("awardDamage", 0),
                "autoSquad": s.get("autoSquad", False),
                "squad_group": squad_group_map.get(sid, 0),
                "clan": s.get("clan") or s.get("clanTag") or "",
                "squadId": sid,
                "squad_color": squad_color_map.get(sid, ""),
            })
        scores_teams.append({
            "id": team_id,
            "player_count": len(rendered),
            "scores": rendered,
            "columns": _build_team_columns(team_id),
        })

    rendered_kills = []
    name_team_map = {s.get("name", ""): s.get("team", "-") for s in scores if isinstance(s, dict)}
    for e in kill_events:
        k_name = e.get("k_name", "-")
        v_name = e.get("v_name", "-")
        rendered_kills.append({
            "t": format_replay_time(e.get("t")),
            "k_name": k_name,
            "k_team": name_team_map.get(k_name, "-"),
            "k_model": e.get("k_model_i18n") or e.get("k_model", "-"),
            "weapon": e.get("weapon_i18n") or e.get("weapon", "-"),
            "v_name": v_name,
            "v_team": name_team_map.get(v_name, "-"),
            "v_model": e.get("v_model_i18n") or e.get("v_model", "-"),
            "destroyed": e.get("destroyed", ""),
            "destroyed_i18n": e.get("destroyed_i18n", ""),
        })

    rendered_vehicles = []
    for v in vehicles:
        if not isinstance(v, dict):
            continue
        vlist = v.get("vehicles", []) or []
        parts = []
        for vh in vlist:
            name = vh.get("model_i18n") or vh.get("model", "?")
            count = vh.get("count", 0)
            parts.append(f"{name} x{count}")
        rendered_vehicles.append({
            "name": v.get("name", "-"),
            "team": v.get("team", "-"),
            "vehicle_text": " / ".join(parts) if parts else "-",
        })

    return {
        "replay_id": data.get("session_id") or result.get("replay_id", "-"),
        "duration": format_replay_time(data.get("duration")),
        "packets": data.get("packets", 0),
        "parse_time_ms": data.get("parse_time_ms", 0),
        "player_count": len(scores),
        "kill_count": len(kill_events),
        "scores_teams": scores_teams,
        "kill_events": rendered_kills,
        "vehicles": rendered_vehicles,
        "hidden_cols": _compute_hidden_cols(scores),
    }


def build_scores_render_data(result):
    data = result.get("data", {}) if isinstance(result, dict) else {}
    scores = data.get("scores", []) or []

    squad_color_map = _assign_squad_colors(scores)
    squad_group_map = _assign_squad_groups(scores)

    grouped = {}
    for s in scores:
        if not isinstance(s, dict):
            continue
        grouped.setdefault(s.get("team", "-"), []).append(s)

    scores_teams = []
    for team_id in sorted(grouped.keys(), key=lambda t: (str(t).isdigit(), str(t))):
        team_scores = grouped[team_id]
        team_scores.sort(key=lambda s: s.get("score", 0), reverse=True)
        rendered = []
        for i, s in enumerate(team_scores):
            sid = s.get("squadId", -1)
            rendered.append({
                "rank": i + 1,
                "name": s.get("name", "-"),
                "kills": s.get("kills", 0),
                "deaths": s.get("deaths", 0),
                "assists": s.get("assists", 0),
                "score": s.get("score", 0),
                "groundKills": s.get("groundKills", 0),
                "captureZone": s.get("captureZone", 0),
                "damageZone": s.get("damageZone", 0),
                "humanKills": s.get("humanKills", 0),
                "teamKills": s.get("teamKills", 0),
                "aiKills": s.get("aiKills", 0),
                "navalKills": s.get("navalKills", 0),
                "missionKills": s.get("missionKills", 0),
                "missileEvades": s.get("missileEvades", 0),
                "shellInterceptions": s.get("shellInterceptions", 0),
                "awardDamage": s.get("awardDamage", 0),
                "autoSquad": s.get("autoSquad", False),
                "squad_group": squad_group_map.get(sid, 0),
                "clan": s.get("clanTag", ""),
                "squadId": sid,
                "squad_color": squad_color_map.get(sid, ""),
            })
        scores_teams.append({
            "id": team_id,
            "player_count": len(rendered),
            "scores": rendered,
            "columns": _build_team_columns(team_id),
        })

    return {
        "replay_id": data.get("session_id", "-"),
        "mission": data.get("mission", "-"),
        "player_count": len(scores),
        "parse_time_ms": data.get("parse_time_ms", 0),
        "scores_teams": scores_teams,
        "hidden_cols": _compute_hidden_cols(scores),
    }