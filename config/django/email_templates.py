# 邮件模板
from enum import Enum

base_email_template = """<!DOCTYPE html>
<html>
<head>
<title>Email Verification Code</title>
<meta charset="utf-8">
<style>
body {
background-color: #f5f5f5;
font-family: Arial, sans-serif;
}
.container {
max-width: 600px;
margin: 0 auto;
padding: 20px;
background-color: #fff;
box-shadow: 0 0 10px rgba(0,0,0,0.3);
border-radius: 5px;
}
h1 {
text-align: center;
font-size: 32px;
color: #333;
margin-top: 0;
}
p {
font-size: 18px;
color: #666;
margin: 10px 0;
line-height: 1.5;
}
#code {
font-size: 24px;
color: #ff6600;
display: inline-block;
margin-bottom: 10px;
}
</style>
</head>
<body>
<div class="container">
<h1>Email Verification Code</h1>
<p>Dear User,</p>
<p>Your verification code is: <strong id="code">{{code}}</strong></p>
<p>Please do not share this code with others. The code is valid for {{expire_time}} minutes.</p>
<p>If you did not request this code, please ignore this email.</p>
<p style="text-align: right;">——From Mentos Proxy</p>
</div>
</body>
</html>"""
notification_email_template = """<!DOCTYPE html>
<html>
<head>
<title>Order Expiration Notification</title>
<meta charset="utf-8">
<style>
body {
background-color: #f5f5f5;
font-family: Arial, sans-serif;
}
.container {
max-width: 600px;
margin: 0 auto;
padding: 20px;
background-color: #fff;
box-shadow: 0 0 10px rgba(0,0,0,0.3);
border-radius: 5px;
}
h1 {
text-align: center;
font-size: 32px;
color: #333;
margin-top: 0;
}
p {
font-size: 18px;
color: #666;
margin: 10px 0;
line-height: 1.5;
}
#code {
font-size: 24px;
color: #ff6600;
display: inline-block;
margin-bottom: 10px;
}
</style>
</head>
<body>
<div class="container">
<h1>Order Expiration Notification</h1>
<p>Dear User,</p>
<p>Your Order <strong id="order_id">{{order_id}}</strong> is about to expire in three days</p>
<p>Please renew it as soon as possible.</p>
<p style="text-align: right;">——From Mentos Proxy</p>
</div>
</body>
</html>"""

delivery_email_template = """<!DOCTYPE html>
<html>
<head>
    <title>You Proxy is Ready</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background-color: #f5f5f5;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
            background-color: #fff;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }
        h1 {
            text-align: center;
            font-size: 28px;
            color: #333;
            margin: 0;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        p {
            font-size: 16px;
            color: #555;
            margin: 15px 0;
            line-height: 1.6;
        }
        #order_id {
            font-weight: bold;
            color: #0066cc;
        }
        .info-card {
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .info-card h2 {
            font-size: 20px;
            color: #333;
            margin: 0 0 15px 0;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 10px;
        }
        .info-card p {
            margin: 10px 0;
            font-size: 15px;
            color: #333;
        }
        .info-card p span {
            font-weight: bold;
            color: #0066cc;
        }
        a {
            display: inline-block;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #0066cc;
            color: #fff;
            text-decoration: none;
            border-radius: 5px;
            text-align: center;
            font-size: 16px;
        }
        a:hover {
            background-color: #005bb5;
        }
        .footer {
            text-align: right;
            font-size: 14px;
            color: #999;
            margin-top: 30px;
            border-top: 1px solid #f0f0f0;
            padding-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>You Proxy is Ready</h1>
        <p>Dear User,</p>
        <p>Your order ID: <span id="order_id">{{order_id}}</span> is ready to use.</p>
        
        <!-- Information Card with Title -->
        <div class="info-card">
            <h2>Information</h2>
            <p>Product: <span id="product">{{product}}</span></p>
            <p>Expired Time: <span id="proxy_expired_at">{{proxy_expired_at}}</span></p>
            <p>Proxy number: <span id="proxy_number">{{proxy_number}}</span> pcs.</p>
        </div>

        <a href="https://www.mentosproxy.com/#/dashboard/index/proxies" target="_blank">Click here to check your order status</a>
        <div class="footer">
            —— From Mentos Proxy
        </div>
    </div>
</body>
</html>
"""

reset_proxy_email_template = """<!DOCTYPE html>
<html>
<head>
    <title>Reset Proxy Task</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background-color: #f5f5f5;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
            background-color: #fff;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }
        h1 {
            text-align: center;
            font-size: 28px;
            color: #333;
            margin: 0;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        p {
            font-size: 16px;
            color: #555;
            margin: 15px 0;
            line-height: 1.6;
        }
        #order_id {
            font-weight: bold;
            color: #0066cc;
        }
        #status {
            font-weight: bold;
            color: #28a745;
        }
        #message {
            font-style: italic;
            color: #888;
        }
        .footer {
            text-align: right;
            font-size: 14px;
            color: #999;
            margin-top: 30px;
            border-top: 1px solid #f0f0f0;
            padding-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Reset Proxy Task</h1>
        <p>Dear User,</p>
        <p>Order ID: <span id="order_id">{{order_id}}</span></p>
        <p>Status: <span id="status">{{status}}</span></p>
        <p>Message: <span id="message">{{message}}</span></p>
        <div class="footer">
            —— From Mentos Proxy
        </div>
    </div>
</body>
</html>
"""

EMAIL_TEMPLATES = {
    'register': {
        'subject': 'Mentos Proxy Registration.',
        "from_email": "Mentos Proxy <info@mentosproxy.com>",
        "html": base_email_template,
    },
    'forgot': {
        'subject': 'Mentos Proxy Reset Password.',
        "from_email": "Mentos Proxy <info@mentosproxy.com>",
        "html": base_email_template,
    },
    'notification': {
        'subject': 'Mentos Proxy nofication.',
        "from_email": "Mentos Proxy <info@mentosproxy.com>",
        "html": notification_email_template,
    },
    'delivery': {
        'subject': 'You Proxy is Ready.',
        "from_email": "Mentos Proxy <info@mentosproxy.com>",
        "html": delivery_email_template,
    },
    'reset_proxy': {
        'subject': 'Order[{{order_id}}] Reset Proxy Task.',
        "from_email": "Mentos Proxy <info@mentosproxy.com>",
        "html": reset_proxy_email_template
    }
}


class EmailTemplate(Enum):
    REGISTER = 'register'
    FORGOT = 'forgot'
    NOTIFICATION = 'notification'
    DELIVERY = 'delivery'
    RESET_PROXY = 'reset_proxy'
