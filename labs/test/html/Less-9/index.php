<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Less-9: Time-based Blind (Game Dev Ver.)</title>
<style>
    /* --- 引入字體 --- */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

    :root {
        --momoi-pink: #FF8F8F;
        --momoi-dark: #D65C5C;
        --midori-green: #7ACC7A;
        --midori-dark: #4E9E4E;
        --bg-color: #F0F4F8;
        --card-bg: #FFFFFF;
        --terminal-bg: #1E1E1E;
    }

    body {
        font-family: 'Nunito', sans-serif;
        background-color: var(--bg-color);
        /* 網格背景 */
        background-image: 
            linear-gradient(rgba(74, 85, 104, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(74, 85, 104, 0.05) 1px, transparent 1px);
        background-size: 20px 20px;
        margin: 0;
        padding-top: 40px;
        color: #4A5568;
    }

    /* 主容器卡片 */
    .container {
        background: var(--card-bg);
        width: 600px;
        margin: 0 auto;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: 4px solid white;
        position: relative;
        overflow: hidden;
        text-align: center;
    }

    /* 頂部裝飾條 (雙子配色) */
    .container::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 8px;
        background: linear-gradient(90deg, var(--momoi-pink) 50%, var(--midori-green) 50%);
    }

    h1 {
        font-weight: 900;
        color: #2D3748;
        margin-bottom: 5px;
    }

    .subtitle {
        color: var(--momoi-dark);
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* --- 表單區域 --- */
    .form-group {
        margin: 20px 0;
        display: flex;
        gap: 10px;
        justify-content: center;
    }

    input[type="text"] {
        width: 70%;
        padding: 12px 15px;
        border: 2px solid #E2E8F0;
        border-radius: 10px;
        font-size: 16px;
        font-family: 'Courier New', monospace;
        outline: none;
        transition: all 0.2s;
    }

    input[type="text"]:focus {
        border-color: var(--midori-green);
        box-shadow: 0 0 0 3px rgba(122, 204, 122, 0.2);
    }

    input[type="submit"] {
        background-color: var(--momoi-pink);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 16px;
        cursor: pointer;
        box-shadow: 0 4px 0 var(--momoi-dark);
        transition: all 0.1s;
    }

    input[type="submit"]:active {
        transform: translateY(4px);
        box-shadow: none;
    }

    input[type="submit"]:hover {
        background-color: #ff7676;
    }

    /* --- 虛擬終端機 --- */
    .terminal-window {
        background-color: var(--terminal-bg);
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        min-height: 100px;
        text-align: left;
        font-family: 'VT323', 'Courier New', monospace;
        border: 2px solid #4A5568;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        position: relative;
    }

    .terminal-header {
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 25px;
        background: #4A5568;
        border-radius: 8px 8px 0 0;
        display: flex;
        align-items: center;
        padding-left: 10px;
    }
    
    .dot { width: 10px; height: 10px; border-radius: 50%; background-color: #FF5F56; margin-right: 5px; }
    .dot:nth-child(2) { background-color: #FFBD2E; }
    .dot:nth-child(3) { background-color: #27C93F; }

    .terminal-content {
        margin-top: 15px;
        font-size: 20px;
        line-height: 1.5;
    }

    .terminal-content font {
        text-shadow: 0 0 5px rgba(255, 255, 0, 0.5);
    }

    .footer-text {
        margin-top: 20px;
        font-size: 12px;
        color: #CBD5E0;
        font-weight: bold;
    }
    
    /* 提示標籤 */
    .hint-tag {
        background-color: #FED7D7;
        color: #C53030;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }

</style>
</head>

<body>

<div class="container">
    <h1>Mission 09</h1>
    <div class="subtitle">Time-based Blind Injection</div>
    
    <div class="hint-tag">⚠️ Note: Output is always the same!</div>

    <div style="font-size: 18px;">
        Welcome Agent <span style="color: var(--momoi-dark); font-weight:bold;">Dhakkan</span>
    </div>

    <!-- 表單區域 -->
    <div class="form-group">
        <form action="" method="GET" style="width: 100%; display: flex; gap: 10px; justify-content: center;">
            <input type="text" name="id" placeholder="Try ?id=1' AND sleep(5) --+" value="<?php echo isset($_GET['id']) ? htmlspecialchars($_GET['id']) : ''; ?>">
            <input type="submit" value="HACK!">
        </form>
    </div>

    <!-- 終端機顯示區域 -->
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
            <span style="color: #ccc; font-size: 12px; margin-left: 10px; font-family: sans-serif;">System Output</span>
        </div>
        
        <div class="terminal-content">
            <?php
            //including the Mysql connect parameters.
            include("../sql-connections/sql-connect.php");
            error_reporting(0);

            // take the variables
            if(isset($_GET['id']))
            {
                $id=$_GET['id'];
                //logging the connection parameters to a file for analysis.
                $fp=fopen('result.txt','a');
                fwrite($fp,'ID:'.$id."\n");
                fclose($fp);

                // connectivity 
                $sql="SELECT * FROM users WHERE id='$id' LIMIT 0,1";
                $result=mysql_query($sql);
                $row = mysql_fetch_array($result);

                if($row)
                {
                    echo '<font size="5" color="#FFFF00">';	
                    echo 'You are in...........';
                    echo "<br>";
                    echo "</font>";
                }
                else 
                {
                    // 注意：這裡即使失敗也顯示 You are in，這是 Time-based 的特徵
                    echo '<font size="5" color="#FFFF00">';
                    echo 'You are in...........';
                    //print_r(mysql_error());
                    //echo "You have an error in your SQL syntax";
                    echo "</br></font>";	
                    echo '<font color= "#0000ff" font size= 3>';	
                }
            }
            else { 
                echo '<span style="color: #7ACC7A;">> Waiting for input...<br>> Hint: Use sleep() to test injection.</span>';
            }
            ?>
        </div>
    </div>

    <div class="footer-text">
        MILLENNIUM SCIENCE SCHOOL - GAME DEVELOPMENT DEPARTMENT
    </div>

</div>

</body>
</html>