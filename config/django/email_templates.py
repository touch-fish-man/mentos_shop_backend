# 邮件模板
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
EMAIL_TEMPLATES = {
    'register': {
        'subject': 'Mentos Proxy Registration.',
        "from_email": "Mentos Proxy <info@mentosproxy.com>",
        "html": base_email_template,
    },
    'frogot': {
        'subject': 'Mentos Proxy Reset Password.',
        "from_email": "Mentos Proxy <info@mentosproxy.com>",
        "html": base_email_template,
    }}
