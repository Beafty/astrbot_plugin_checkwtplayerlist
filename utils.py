import json
import csv
from pathlib import Path
from functools import lru_cache

UNIT_ID_COLUMN = "<ID|readonly|noverify>"
ZH_NAME_COLUMNS = ("<Chinese>", "<TChinese>", "<HChinese>")

def get_unit_id(row: dict) -> str:
    return (row.get(UNIT_ID_COLUMN) or "").strip().strip('"')

def get_unit_zh_name(row: dict) -> str:
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
            unit_id = get_unit_id(row)
            zh_name = get_unit_zh_name(row)

            if not unit_id or not zh_name:
                continue

            units_name_map[unit_id] = zh_name

            if unit_id.endswith("_shop"):
                units_name_map[unit_id[:-5]] = zh_name

    return units_name_map

def translate_unit_name(name: str):
    if not name:
        return name
    name = str(name).strip()
    mp = load_units_name_map()

    if name in mp:
        return mp[name]

    return mp.get(name.split("/")[-1], name)

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
            ctype = craft.get("type") or ""
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