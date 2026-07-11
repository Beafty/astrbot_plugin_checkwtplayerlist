ROOM_TEMPLATE = '''
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face {
    font-family: "SkyquakeSymbols";
    src: url("data:font/ttf;base64,{{ skyquake_font_base64 }}") format("truetype");
}
* {
    box-sizing: border-box;
}
body {
    margin: 0;
    width: max-content;
    min-width: 700px;
    font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    color: #18212f;
    background: #edf1f5;
}
.page {
    padding: 32px;
    width: max-content;
}
/* 顶部 */
header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 24px;
    padding: 26px 30px;
    color: #f8fafc;
    background: linear-gradient(135deg, #22314a, #475b36);
    border-radius: 8px;
}
h1 {
    margin: 0 0 8px;
    font-size: 34px;
}
.meta {
    display: flex;
    gap: 12px;
}
.badge {
    padding: 7px 12px;
    border: 1px solid rgba(255,255,255,.28);
    border-radius: 999px;
}
.count {
    text-align: right;
}
.count strong {
    display: block;
    font-size: 38px;
}
.count span {
    color: #dce7ee;
    font-size: 14px;
}
/* 队伍 */
.teams-container {
    display: flex;
    gap: 18px;
    width: max-content;
}
.team-section {
    width: max-content;
    background: white;
    border: 1px solid #d8dee8;
    border-radius: 8px;
    overflow: hidden;
}
h2 {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0;
    padding: 16px 20px;
    font-size: 20px;
    background: #f8fafc;
}
h2 span {
    font-size: 14px;
    color: #617086;
    font-weight: 500;
}
/* 表格 */
table {
    width: max-content;
    border-collapse: collapse;
    table-layout: auto;
}
th {
    padding: 11px 12px;
    color: #617086;
    font-size: 13px;
    text-align: left;
    background: #fbfcfe;
    border-top: 1px solid #e5e9f0;
    border-bottom: 1px solid #e5e9f0;
}
td {
    padding: 12px;
    border-bottom: 1px solid #edf0f4;
    vertical-align: middle;
    font-size: 14px;
    white-space: nowrap;
}
tr:last-child td {
    border-bottom: 0;
}
/* 序号 */
.num {
    text-align: center;
    color: #3f4d60;
    font-variant-numeric: tabular-nums;
}
/* 玩家 */
.player {
    max-width: 220px;
}
.player span {
    display: block;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 700;
    color: #111827;
}
.player small {
    display: block;
    margin-top: 3px;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #6b7280;
    font-size: 12px;
}
/* 载具 */
.craft {
    font-family:
        "SkyquakeSymbols",
        "Microsoft YaHei",
        Arial,
        sans-serif;

    padding: 2px 0;
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.craft:not(:last-child){
    border-bottom: 1px dashed #e5e7eb;
}
/* 空 */
.empty {
    margin-top: 18px;
    padding: 28px;
    text-align: center;
    background: #fff;
    border: 1px solid #d8dee8;
    border-radius: 8px;
    color: #617086;
}
</style>
</head>

<body>
<div class="page">
    <header>
        <div>
            <h1>玩家列表</h1>
            <div class="meta">
                <span class="badge">房间 {{ room_id|e }}</span>
                <span class="badge">服务器 {{ cluster|e }}</span>
            </div>
        </div>
        <div class="count">
            <strong>{{ player_count }}</strong>
            <span>players</span>
        </div>
    </header>

    <div class="teams-container">
        {% for team in teams %}
        <section class="team-section">
            <h2>队伍 {{ team.id|e }} <span>{{ team.players|length }} 人</span></h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>玩家</th>
                        <th>载具</th>
                        <th>国家</th>
                        <th>平台</th>
                        <th>小队</th>
                        <th>Tier</th>
                        <th>最高BR</th>
                    </tr>
                </thead>
                <tbody>
                    {% for player in team.players %}
                    <tr>
                        <td class="num">{{ loop.index }}</td>
                        <td>
                            <div class="player">
                                <span>{{ player.name|e }}</span>
                                <small>{{ player.clan|e }} · ID {{ player.id|e }}</small>
                            </div>
                        </td>
                        <td>{{ player.crafts|safe }}</td>
                        <td>{{ player.country|e }}</td>
                        <td>{{ player.platform|e }}</td>
                        <td class="num">{{ player.squad|e }}</td>
                        <td class="num">{{ player.tier|e }}</td>
                        <td class="num">{{ player.BR|e }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
        {% endfor %}
    </div>

    {% if not teams %}
    <div class="empty">未在 JSON 的 public 字段中找到玩家列表</div>
    {% endif %}
</div>
</body>
</html>
'''