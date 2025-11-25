<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>SQLi-lab</title>
<style>
:root {
    --nozomi-red: #E63E62;
    --hikari-green: #00B894;
    --bg-color: #2D3436;
    --card-bg: #FFFFFF;
    --terminal-bg: #1E272E;
    --text-main: #2D3436;
}
body {
    margin: 0;
    padding: 0;
    font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: var(--bg-color);
    background-image: 
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 30px 30px;
    overflow: hidden;
}
body::after {
    content: "";
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(
        to bottom,
        transparent 50%,
        rgba(0, 255, 150, 0.02) 50%,
        rgba(0, 255, 150, 0.05) 51%,
        transparent 52%
    );
    background-size: 100% 10px;
    animation: scanline 8s linear infinite;
    pointer-events: none;
    z-index: 999;
}
@keyframes scanline {
    0% { background-position: 0 -100vh; }
    100% { background-position: 0 100vh; }
}
.container {
    background: var(--card-bg);
    padding: 40px 50px;
    border-radius: 8px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    text-align: center;
    max-width: 600px;
    width: 90%;
    position: relative;
    border-left: 8px solid var(--nozomi-red);
    border-right: 8px solid var(--hikari-green);
    opacity: 0;
    animation: slideIn 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}
@keyframes slideIn {
    from { opacity: 0; transform: translateY(30px) scale(0.95); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}
.container::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 6px;
    background: linear-gradient(90deg, var(--nozomi-red) 50%, var(--hikari-green) 50%);
}
.status-light {
    position: absolute;
    top: 15px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    box-shadow: 0 0 5px currentColor;
}
.light-nozomi {
    left: 15px;
    background-color: var(--nozomi-red);
    color: var(--nozomi-red);
    animation: blink 3s infinite ease-in-out;
}
.light-hikari {
    right: 15px;
    background-color: var(--hikari-green);
    color: var(--hikari-green);
    animation: blink 4s infinite ease-in-out 1s;
}
@keyframes blink {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.2); box-shadow: 0 0 10px currentColor; }
}
h1 {
    color: var(--text-main);
    margin: 10px 0;
    font-size: 1.8em;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.subtitle {
    display: inline-block;
    font-size: 1.2em;
    color: #636e72;
    background: #f1f2f6;
    padding: 4px 12px;
    border-radius: 4px;
    margin-bottom: 20px;
    font-weight: bold;
}
.mission-info {
    background-color: #fafafa;
    border: 1px solid #eee;
    padding: 15px;
    border-radius: 5px;
    font-size: 0.95em;
    color: #555;
    text-align: left;
    margin-bottom: 25px;
    line-height: 1.6;
}
.form-group {
    margin-bottom: 20px;
}
input[type="text"] {
    padding: 12px 15px;
    border: 2px solid #dfe6e9;
    border-radius: 4px;
    font-size: 1em;
    width: 60%;
    transition: border-color 0.3s;
    outline: none;
}
input[type="text"]:focus {
    border-color: var(--hikari-green);
}
button[type="submit"] {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    padding: 12px 25px;
    background-color: var(--nozomi-red);
    color: white;
    border: none;
    border-bottom: 4px solid #c0392b;
    border-radius: 4px;
    font-size: 1em;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    text-transform: uppercase;
    position: relative;
    overflow: hidden;
}
button[type="submit"]::before {
    content: '▶';
    display: inline-block;
    opacity: 0;
    max-width: 0;
    transform: translateX(-20px);
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    margin-right: 0;
}
button[type="submit"]:hover::before {
    opacity: 1;
    max-width: 20px;
    transform: translateX(0);
    margin-right: 8px;
}
button[type="submit"]::after {
    content: '';
    position: absolute;
    top: 0; left: -100%; width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    transition: 0.5s;
}
button[type="submit"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(230, 62, 98, 0.4);
}
button[type="submit"]:hover::after {
    left: 100%;
}
button[type="submit"]:active {
    transform: translateY(2px);
    border-bottom: 2px solid #c0392b;
}
.terminal-content {
    background-color: var(--terminal-bg);
    color: #ecf0f1;
    padding: 20px;
    border-radius: 4px;
    border-left: 4px solid var(--hikari-green);
    text-align: left;
    min-height: 60px;
    font-family: 'Consolas', 'Monaco', monospace;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}
.status-success {
    color: var(--hikari-green);
    font-weight: bold;
    border-left: 3px solid var(--hikari-green);
    padding-left: 10px;
    animation: fadeIn 0.5s ease-out;
}
.status-fail {
    color: var(--nozomi-red);
    border-left: 3px solid var(--nozomi-red);
    padding-left: 10px;
    animation: fadeIn 0.5s ease-out;
}
.status-wait {
    color: #7f8c8d;
    animation: fadeIn 0.5s ease-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateX(-5px); }
    to { opacity: 1; transform: translateX(0); }
}
</style>
</head>

<body>

<div class="container">
    <div class="status-light light-nozomi" title="Nozomi Online"></div>
    <div class="status-light light-hikari" title="Hikari Online"></div>

    <div class="subtitle">目標 : 取得張胖胖的使用者密碼</div>

    <div class="mission-info">
        經調查我們已知下面資訊<br>
        - 搜尋欄存在SQL注入的漏洞<br>
        - 在資料庫中有一個資料表為 "users" 裡面存放了使用者資訊<br>
        - 使用者密碼為數字加英文字母的組合<br>
        - 張胖胖平常喜歡用 "jack" 當使用者名稱
    </div>

    <div class="form-group">
        <form action="" method="GET" style="width: 100%; display: flex; gap: 10px; justify-content: center;">
            <input type="text" name="id" placeholder="輸入ID進行查詢" value="<?php echo isset($_GET['id']) ? htmlspecialchars($_GET['id']) : ''; ?>">
            <button type="submit">Search</button>
        </form>
    </div>

    <div class="terminal-content">
        <?php
        ob_start(); 
        include("../sql-connections/setup-db.php"); 
        ob_end_clean(); 
        include("../sql-connections/sql-connect.php");
        error_reporting(0);

        if(isset($_GET['id']))
        {
            $id=$_GET['id'];
            $sql="SELECT * FROM users WHERE id='$id' LIMIT 0,1";
            $result=mysql_query($sql);
            $row = mysql_fetch_array($result);

            if($row)
            {
                echo '<div class="status-success">';
                echo '> [SYSTEM]: Query Success<br>';
                echo '> DATA RETRIEVED.';
                echo '</div>';
            }
            else 
            {
                echo '';
            }
        }
        else { 
            echo '<div class="status-wait">';
            echo '> SYSTEM READY...<br>> WAITING FOR INPUT.';
            echo '</div>';
        }
        ?>
    </div>

</div>

</body>
</html>
