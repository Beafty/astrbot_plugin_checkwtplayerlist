import json

def check_room_id(room_id: str):
    if room_id is None:
        return False
    return (
        len(room_id) == 15
        and all(c in "0123456789abcdef" for c in room_id)
    )

def convert_mrank_to_br(mrank: str):
    """将战雷内部整型 mrank 转换为玩家熟知的 BR（如 34 -> 11.3）"""
    if mrank is None or mrank == "":
        return "-"
    try:
        mrank_int = int(mrank)
        int_part = mrank_int // 3
        rem = mrank_int % 3
        frac = "0" if rem == 0 else ("3" if rem == 1 else "7")
        return f"{int_part}.{frac}"
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
    public = room_data.get("public", {}) if isinstance(room_data, dict) else {}
    if not isinstance(public, dict):
        return []
    players = [
        p for p in public.values()
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
            name = craft.get("name") or "未知载具"
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
        return ", ".join(str(v) for _, v in sorted(crafts.items()))
    return "-"

def format_api_result(result):
    room_data, _ = extract_room_payload(result)
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

def build_room_render_data(result):
    room_data, _ = extract_room_payload(result)
    players = get_players(room_data)
    room_id = room_data.get("roomId") or room_data.get("room_id") or room_data.get("id") or "-"
    grouped = {}
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
    }