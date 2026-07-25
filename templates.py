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
.footer {
    padding-top: 8px;
    color: #1B5E20;
    font-size: 32px;
    text-align: center;
    line-height: 0.5;
}
.footer2{
    padding-left: 18px;
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
.player small .clan {
    font-family: "SkyquakeSymbols", "Microsoft YaHei", Arial, sans-serif;
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
                                <small><span class="clan">{{ player.clan|e }}</span> · ID {{ player.id|e }}</small>
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
<div class="footer">
    <p>使用方法：在群内发送/room加左下角房间号或当前游戏界面截图。</p>
    <p>Beta Test! 限时测试中，拉机器人入群即可使用。（推荐在联队赛猜测对方阵容时候使用）</p>
    <p>Powered by AstrBotWTcheck</p>
</div>
<div class="footer2">
    <p>插件已开源:github.com/Beafty/astrbot_plugin_checkwtplayerlist</p>
</div>
</body>
</html>
'''

REPLAY_TEMPLATE = '''
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
* { box-sizing: border-box; }
body {
    margin: 0; width: max-content; min-width: 780px;
    font-family: "SkyquakeSymbols", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    color: #18212f; background: #edf1f5;
}
.page { padding: 28px; width: max-content; }
section {
    margin-top: 16px; background: white;
    border: 1px solid #d8dee8; border-radius: 8px; overflow: hidden;
}
header {
    padding: 24px 28px; color: #f8fafc;
    background: linear-gradient(135deg, #2a3f5f, #6b3a2a); border-radius: 8px;
}
h1 { margin: 0 0 8px; font-size: 30px; }
.meta { display: flex; flex-wrap: wrap; gap: 10px; }
.badge {
    padding: 5px 12px; border: 1px solid rgba(255,255,255,.28);
    border-radius: 999px; font-size: 13px;
}
h2 {
    display: flex; justify-content: space-between; align-items: center;
    margin: 0; padding: 14px 20px; font-size: 18px;
    background: #f8fafc; border-bottom: 1px solid #e5e9f0;
}
h2 span { font-size: 13px; color: #617086; font-weight: 500; }
.teams-container { display: flex; gap: 14px; width: max-content; }
.team-section { width: max-content; }
.team-section h3 {
    margin: 0; padding: 10px 16px; font-size: 15px;
    background: #f8fafc; border-bottom: 1px solid #e5e9f0;
}
.team-section h3 span { font-size: 12px; color: #617086; font-weight: 500; margin-left: 8px; }
table { width: 100%; border-collapse: collapse; table-layout: auto; }
th {
    padding: 9px 10px; color: #617086; font-size: 12px; text-align: center;
    background: #fbfcfe; border-bottom: 1px solid #e5e9f0; white-space: nowrap;
}
td {
    padding: 10px; border-bottom: 1px solid #edf0f4;
    vertical-align: middle; font-size: 13px; white-space: nowrap;
}
tr:last-child td { border-bottom: 0; }
.num { text-align: center; color: #3f4d60; font-variant-numeric: tabular-nums; }
.kill-list { padding: 14px 20px; line-height: 1.8; }
.kill-item { padding: 3px 0; font-size: 13px; border-bottom: 1px solid #f0f2f5; }
.kill-item:last-child { border-bottom: 0; }
.vehicles-list { padding: 14px 20px; }
.vehicles-list .v-item { padding: 6px 0; font-size: 13px; border-bottom: 1px solid #f0f2f5; }
.vehicles-list .v-item:last-child { border-bottom: 0; }
.vehicles-list .v-name { font-weight: 600; color: #111827; }
.vehicles-list .v-text { color: #4a5568; margin-left: 8px; }
.empty { padding: 24px; text-align: center; color: #617086; }
</style>
</head>

<body>
<div class="page">
    <header>
        <h1>回放详情</h1>
        <div class="meta">
            <span class="badge">ID {{ replay_id|e }}</span>
            <span class="badge">时长 {{ duration|e }}</span>
            <span class="badge">{{ packets }} 数据包</span>
            <span class="badge">解析 {{ parse_time_ms }}ms</span>
        </div>
    </header>

    {% if scores_teams %}
    <section>
        <h2>记分板 <span>{{ player_count }} 人</span></h2>
        <div class="teams-container">
            {% for team in scores_teams %}
            <div class="team-section">
                <h3>队伍 {{ team.id }}<span>{{ team.player_count }} 人</span></h3>
                <table>
                    <thead>
                        <tr>
                            {% for col in team.columns %}
                                {% if col.key == '_name' or col.key not in hidden_cols %}
                                    <th>{{ col.label }}</th>
                                {% endif %}
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in team.scores %}
                        <tr{% if s.squad_color %} style="background-color:{{ s.squad_color }}"{% endif %}>
                            {% for col in team.columns %}
                                {% if col.key == '_name' or col.key not in hidden_cols %}
                                    <td class="num">
                                        {% if col.key == '_name' %}
                                            <span style="color:{% if team.id in (1, '1') %}#2563eb{% elif team.id in (2, '2') %}#dc2626{% else %}#000{% endif %};font-weight:600">{% if s.clan %}{{ s.clan|e }} {% endif %}{{ s.name|e }}</span>
                                        {% elif col.key == 'autoSquad' %}
                                            {% if s.squad_group %}{{ s.squad_group }}{% endif %}
                                        {% else %}
                                            {{ s[col.key] }}
                                        {% endif %}
                                    </td>
                                {% endif %}
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}

    {% if kill_events %}
    <section>
        <h2>击杀事件 <span>{{ kill_count }} 次</span></h2>
        <div class="kill-list">
            {% for e in kill_events %}
            <div class="kill-item">
                {% if e.destroyed %}
                    {{ e.t|e }} <span style="color:{% if e.k_team in (1, '1') %}#2563eb{% elif e.k_team in (2, '2') %}#dc2626{% else %}#000{% endif %};font-weight:600">{{ e.k_name|e }}</span>({{ e.k_model|e }})使用{{ e.weapon|e }}击毁了{{ e.destroyed_i18n or e.destroyed }}
                {% elif e.k_name == '<pid=-1>' %}
                    {{ e.t|e }} <span style="color:{% if e.v_team in (1, '1') %}#2563eb{% elif e.v_team in (2, '2') %}#dc2626{% else %}#000{% endif %};font-weight:600">{{ e.v_name|e }}</span>已被摧毁
                {% elif e.k_name == '<pid=-2>' %}
                    {{ e.t|e }} <span style="color:{% if e.v_team in (1, '1') %}#2563eb{% elif e.v_team in (2, '2') %}#dc2626{% else %}#000{% endif %};font-weight:600">{{ e.v_name|e }}</span>离开了载具
                {% else %}
                    {{ e.t|e }} <span style="color:{% if e.k_team in (1, '1') %}#2563eb{% elif e.k_team in (2, '2') %}#dc2626{% else %}#000{% endif %};font-weight:600">{{ e.k_name|e }}</span>({{ e.k_model|e }})使用{{ e.weapon|e }}击毁了<span style="color:{% if e.v_team in (1, '1') %}#2563eb{% elif e.v_team in (2, '2') %}#dc2626{% else %}#000{% endif %};font-weight:600">{{ e.v_name|e }}</span>({{ e.v_model|e }})
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}

    {% if vehicles %}
    <section>
        <h2>载具使用</h2>
        <div class="vehicles-list">
            {% for v in vehicles %}
            <div class="v-item">
                <span class="v-name" style="color:{% if v.team in (1, '1') %}#2563eb{% elif v.team in (2, '2') %}#dc2626{% else %}#000{% endif %}">{{ v.name|e }}</span>
                <span class="v-text">{{ v.vehicle_text|e }}</span>
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}

    {% if not scores_teams and not kill_events and not vehicles %}
    <section><div class="empty">回放数据为空</div></section>
    {% endif %}
</div>
</body>
</html>
'''

SCORES_TEMPLATE = '''
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
* { box-sizing: border-box; }
body {
    margin: 0; width: max-content; min-width: 640px;
    font-family: "SkyquakeSymbols", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    color: #18212f; background: #edf1f5;
}
.page { padding: 24px; width: max-content; }
section {
    margin-top: 14px; background: white;
    border: 1px solid #d8dee8; border-radius: 8px; overflow: hidden;
}
header {
    padding: 20px 24px; color: #f8fafc;
    background: linear-gradient(135deg, #2a3f5f, #5a3a2a); border-radius: 8px;
}
h1 { margin: 0 0 6px; font-size: 26px; }
.meta { display: flex; flex-wrap: wrap; gap: 8px; }
.badge {
    padding: 4px 10px; border: 1px solid rgba(255,255,255,.28);
    border-radius: 999px; font-size: 12px;
}
h2 {
    display: flex; justify-content: space-between; align-items: center;
    margin: 0; padding: 12px 18px; font-size: 16px;
    background: #f8fafc; border-bottom: 1px solid #e5e9f0;
}
h2 span { font-size: 12px; color: #617086; font-weight: 500; }
.teams-container { display: flex; gap: 12px; width: max-content; }
.team-section { width: max-content; }
.team-section h3 {
    margin: 0; padding: 8px 14px; font-size: 14px;
    background: #f8fafc; border-bottom: 1px solid #e5e9f0;
}
.team-section h3 span { font-size: 11px; color: #617086; font-weight: 500; margin-left: 6px; }
table { width: 100%; border-collapse: collapse; table-layout: auto; }
th {
    padding: 7px 8px; color: #617086; font-size: 11px; text-align: center;
    background: #fbfcfe; border-bottom: 1px solid #e5e9f0; white-space: nowrap;
}
td {
    padding: 8px; border-bottom: 1px solid #edf0f4;
    vertical-align: middle; font-size: 12px; white-space: nowrap;
}
tr:last-child td { border-bottom: 0; }
.num { text-align: center; color: #3f4d60; font-variant-numeric: tabular-nums; }
.empty { padding: 20px; text-align: center; color: #617086; }
</style>
</head>

<body>
<div class="page">
    <header>
        <h1>记分板</h1>
        <div class="meta">
            <span class="badge">ID {{ replay_id|e }}</span>
            <span class="badge">{{ mission|e }}</span>
            <span class="badge">解析 {{ parse_time_ms }}ms</span>
        </div>
    </header>

    {% if scores_teams %}
    <section>
        <h2>队伍对比 <span>{{ player_count }} 人</span></h2>
        <div class="teams-container">
            {% for team in scores_teams %}
            <div class="team-section">
                <h3>队伍 {{ team.id }}<span>{{ team.player_count }} 人</span></h3>
                <table>
                    <thead>
                        <tr>
                            {% for col in team.columns %}
                                {% if col.key == '_name' or col.key not in hidden_cols %}
                                    <th>{{ col.label }}</th>
                                {% endif %}
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in team.scores %}
                        <tr{% if s.squad_color %} style="background-color:{{ s.squad_color }}"{% endif %}>
                            {% for col in team.columns %}
                                {% if col.key == '_name' or col.key not in hidden_cols %}
                                    <td class="num">
                                        {% if col.key == '_name' %}
                                            <span style="color:{% if team.id in (1, '1') %}#2563eb{% elif team.id in (2, '2') %}#dc2626{% else %}#000{% endif %};font-weight:600">{% if s.clan %}{{ s.clan|e }} {% endif %}{{ s.name|e }}</span>
                                        {% elif col.key == 'autoSquad' %}
                                            {% if s.squad_group %}{{ s.squad_group }}{% endif %}
                                        {% else %}
                                            {{ s[col.key] }}
                                        {% endif %}
                                    </td>
                                {% endif %}
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endfor %}
        </div>
    </section>
    {% else %}
    <section><div class="empty">记分板数据为空</div></section>
    {% endif %}
</div>
</body>
</html>
'''