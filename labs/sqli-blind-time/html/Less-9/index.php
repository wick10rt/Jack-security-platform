<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>SQLi-lab</title>
<style>
    :root {
        --mika-pink: #FFC0CB;
        --mika-deep: #F48FB1;
        --nagisa-gold: #D4AF37;
        --nagisa-tea: #FFF8E1;
        --seia-orange: #FFCC80;
        --text-elegant: #5D4037;
        --terminal-bg: #2D3436;
    }

    body {
        margin: 0;
        padding: 0;
        font-family: 'Georgia', 'Times New Roman', serif;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        background: linear-gradient(135deg, #FFF0F5 0%, #E3F2FD 100%);
        overflow: hidden;
        color: var(--text-elegant);
    }

    body::before, body::after {
        content: "🪶";
        position: absolute;
        top: -10%;
        font-size: 20px;
        color: rgba(255, 255, 255, 0.6);
        text-shadow: 0 0 5px rgba(255, 192, 203, 0.5);
        animation: feather-fall 10s linear infinite;
        z-index: -1;
    }
    body::after {
        left: 70%;
        animation-duration: 15s;
        animation-delay: 2s;
        font-size: 30px;
    }
    .feather-extra {
        position: absolute;
        top: -10%;
        color: rgba(255, 255, 255, 0.8);
        animation: feather-fall 12s linear infinite;
        z-index: -1;
    }

    @keyframes feather-fall {
        0% { transform: translateY(0) rotate(0deg) translateX(0); opacity: 0; }
        10% { opacity: 1; }
        100% { transform: translateY(110vh) rotate(360deg) translateX(50px); opacity: 0; }
    }

    .container {
        background: rgba(255, 255, 255, 0.95);
        padding: 40px 50px;
        border-radius: 15px;
        border: 1px solid white;
        outline: 4px double var(--nagisa-gold);
        outline-offset: -10px;
        box-shadow: 
            0 20px 50px rgba(212, 175, 55, 0.2),
            0 0 0 10px rgba(255, 255, 255, 0.5);
        text-align: center;
        max-width: 600px;
        width: 90%;
        position: relative;
        backdrop-filter: blur(5px);
        animation: float-in 1s ease-out;
    }

    @keyframes float-in {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .container::before {
        content: '⏳';
        font-size: 2em;
        position: absolute;
        top: -25px;
        left: 50%;
        transform: translateX(-50%);
        background: #FFF0F5;
        padding: 0 15px;
        border-radius: 50%;
        box-shadow: 0 0 15px var(--nagisa-gold);
    }

    h1 {
        font-size: 2.2em;
        margin: 10px 0;
        font-weight: normal;
        letter-spacing: 2px;
        background: linear-gradient(to right, var(--mika-pink), var(--nagisa-gold));
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
    }

    .subtitle {
        font-size: 1.5em;
        color: #8D6E63;
        font-style: italic;
        margin-bottom: 20px;
        letter-spacing: 1px;
    }

    .form-group {
        margin-bottom: 25px;
    }

    input[type="text"] {
        padding: 12px 15px;
        border: 2px solid #EEE;
        border-radius: 50px;
        font-size: 1em;
        width: 60%;
        font-family: 'Georgia', serif;
        transition: all 0.3s;
        outline: none;
        background: #FAFAFA;
    }

    input[type="text"]:focus {
        border-color: var(--nagisa-gold);
        background: white;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
    }

    button[type="submit"] {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        padding: 12px 25px;
        background: linear-gradient(135deg, var(--mika-pink), #F8BBD0);
        color: white;
        border: none;
        border-radius: 50px;
        font-size: 1em;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-transform: uppercase;
        position: relative;
        overflow: hidden;
        font-family: 'Georgia', serif;
        box-shadow: 0 5px 15px rgba(255, 192, 203, 0.6);
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

    button[type="submit"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 192, 203, 0.8);
        background: linear-gradient(135deg, var(--mika-deep), var(--mika-pink));
    }

    .terminal-window {
        background: var(--terminal-bg);
        border-radius: 8px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 2px solid var(--nagisa-gold);
        overflow: hidden;
        text-align: left;
        margin-top: 20px;
        position: relative;
    }

    .terminal-header {
        background: #222;
        padding: 8px 15px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #444;
    }

    .dot {
        width: 10px; height: 10px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .dot:nth-child(1) { background: #FF5F56; }
    .dot:nth-child(2) { background: #FFBD2E; }
    .dot:nth-child(3) { background: #27C93F; }

    .terminal-content {
        padding: 20px;
        min-height: 80px;
        color: #ecf0f1;
        font-family: 'Consolas', 'Monaco', monospace;
    }

    .status-success {
        color: var(--nagisa-gold);
        font-weight: bold;
        border-left: 3px solid var(--nagisa-gold);
        padding-left: 10px;
        animation: fadeIn 0.5s ease-out;
    }

    .status-fail {
        color: var(--mika-deep);
        font-weight: bold;
        border-left: 3px solid var(--mika-deep);
        padding-left: 10px;
        animation: fadeIn 0.5s ease-out;
    }

    .status-wait {
        color: #7ACC7A;
        animation: pulse 2s infinite;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-5px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }

</style>
</head>

<body>

<div class="feather-extra" style="left: 20%; animation-delay: 0s;">🪶</div>
<div class="feather-extra" style="left: 50%; animation-delay: 5s;">🪶</div>
<div class="feather-extra" style="left: 80%; animation-delay: 3s;">🪶</div>

<div class="container">
    <h1>目標</h1>
    <div class="subtitle">取得張胖胖的使用者密碼</div>

    <div style="font-size: 1.1em; margin-bottom: 20px; text-align: left; padding: 0 20px; line-height: 1.6;">
       <strong style="color: var(--text-elegant);">經調查我們已知下面資訊：</strong><br>
       - 搜尋欄存在 SQL 注入的漏洞<br>
       - 在資料庫中有一個資料表為 <code style="background: #FFF3E0; padding: 2px 5px; border-radius: 4px; color: #E65100;">users</code> 儲存使用者資訊<br>
       - 使用者密碼為數字加英文字母的組合<br>
       - 張胖胖平常喜歡用 <code style="background: #FFF3E0; padding: 2px 5px; border-radius: 4px; color: #E65100;">jack</code> 當使用者名稱 
    </div>

    <div class="form-group">
        <form action="" method="GET" style="width: 100%; display: flex; gap: 10px; justify-content: center;">
            <input type="text" name="id" placeholder="輸入ID進行查詢" value="<?php echo isset($_GET['id']) ? htmlspecialchars($_GET['id']) : ''; ?>">
            <button type="submit">SEARCH</button>
        </form>
    </div>

    <div class="terminal-window">
        <div class="terminal-header">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
            <span style="color: #bbb; font-size: 12px; margin-left: 10px; font-family: sans-serif; letter-spacing: 1px;">SYSTEM_OUTPUT</span>
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
                    echo '> [TEA_PARTY]: Success...<br>';
                    echo '> Welcome to the Garden.';
                    echo '</div>';
                }
                else 
                {
                    echo '<div class="status-success">';
                    echo '> [TEA_PARTY]: Success...<br>';
                    echo '> Welcome to the Garden.';
                    echo '</div>';	
                }
            }
            else { 
                echo '<div class="status-wait">';
                echo '> SYSTEM READY...<br>> WAITING FOR INPUT...';
                echo '</div>';
            }
            ?>
        </div>
    </div>

</div>

</body>
</html>
