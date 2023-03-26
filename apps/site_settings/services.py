from django.conf import settings
def change_site_settings(request):
    discord_cliend_id = int(request.data.get("discord_cliend_id"))
    discord_secret = request.data.get("discord_secret")
    discord_redirect_url = request.data.get("discord_redirect_url")
    discord_bind_redirect_url = request.data.get("discord_bind_redirect_url")
    api_key = request.data.get("api_key")
    api_scert = request.data.get("api_scert")
    app_password = request.data.get("app_password")
    shop_url = request.data.get("shop_url")
    email_method = request.data.get("email_method")
    email_code_expire = int(request.data.get("email_code_expire"))
    email_backend = request.data.get("email_backend")
    sendgrid_api_key = request.data.get("sendgrid_api_key")
    mailgun_api_key = request.data.get("mailgun_api_key")
    mailgun_sender_domain = request.data.get("mailgun_sender_domain")
    twitter = request.data.get("twitter")
    discord = request.data.get("discord")
    invite_level_points_per_user = int(request.data.get("invite_level_points_per_user"))
    billing_rate = float(request.data.get("billing_rate"))
    level_points_to_upgrade = int(request.data.get("level_points_to_upgrade"))
    level_points_decay_rate = float(request.data.get("level_points_decay_rate"))
    level_points_decay_day = int(request.data.get("level_points_decay_day"))
    min_level = int(request.data.get("min_level"))
    max_level = int(request.data.get("max_level"))
    level_discount_rate = float(request.data.get("level_discount_rate"))
    invite_rebate_rate = float(request.data.get("invite_rebate_rate"))

    settings.DISCORD_CLIENT_ID = discord_cliend_id
    settings.DISCORD_CLIENT_SECRET = discord_secret
    settings.DISCORD_REDIRECT_URI = discord_redirect_url
    settings.DISCORD_BIND_REDIRECT_URI = discord_bind_redirect_url
    settings.SHOPIFY_API_KEY = api_key
    settings.SHOPIFY_API_SECRET = api_scert
    settings.SHOPIFY_APP_KEY = app_password
    settings.SHOPIFY_SHOP_URL = shop_url
    settings.EMAIL_METHOD = email_method
    settings.EMAIL_CODE_EXPIRE = email_code_expire
    settings.EMAIL_BACKEND = email_backend
    settings.SENDGRID_API_KEY = sendgrid_api_key
    settings.MAILGUN_API_KEY = mailgun_api_key
    settings.MAILGUN_SENDER_DOMAIN = mailgun_sender_domain        
    settings.SUPPORT_TWITTER = twitter
    settings.SUPPORT_DISCORD = discord
    settings.INVITE_LEVEL_POINTS_PER_USER = invite_level_points_per_user
    settings.BILLING_RATE = billing_rate
    settings.LEVEL_POINTS_TO_UPGRADE = level_points_to_upgrade
    settings.LEVEL_POINTS_DECAY_RATE = level_points_decay_rate
    settings.LEVEL_POINTS_DECAY_DAY = level_points_decay_day
    settings.MIN_LEVEL = min_level
    settings.MAX_LEVEL = max_level
    settings.LEVEL_DISCOUNT_RATE = level_discount_rate
    settings.INVITE_REBATE_RATE = invite_rebate_rate

def save_site_settings(request,file):
    """
    保存网站设置
    """
    discord_cliend_id = int(request.data.get("discord_cliend_id"))
    discord_secret = request.data.get("discord_secret")
    discord_redirect_url = request.data.get("discord_redirect_url")
    discord_bind_redirect_url = request.data.get("discord_bind_redirect_url")
    api_key = request.data.get("api_key")
    api_scert = request.data.get("api_scert")
    app_password = request.data.get("app_password")
    shop_url = request.data.get("shop_url")
    email_method = request.data.get("email_method")
    email_code_expire = int(request.data.get("email_code_expire"))
    email_backend = request.data.get("email_backend")
    sendgrid_api_key = request.data.get("sendgrid_api_key")
    mailgun_api_key = request.data.get("mailgun_api_key")
    mailgun_sender_domain = request.data.get("mailgun_sender_domain")
    twitter = request.data.get("twitter")
    discord = request.data.get("discord")
    invite_level_points_per_user = int(request.data.get("invite_level_points_per_user"))
    billing_rate = float(request.data.get("billing_rate"))
    level_points_to_upgrade = int(request.data.get("level_points_to_upgrade"))
    level_points_decay_rate = float(request.data.get("level_points_decay_rate"))
    level_points_decay_day = int(request.data.get("level_points_decay_day"))
    min_level = int(request.data.get("min_level"))
    max_level = int(request.data.get("max_level"))
    level_discount_rate = float(request.data.get("level_discount_rate"))
    invite_rebate_rate = float(request.data.get("invite_rebate_rate"))

    settings_var = ['DISCORD_CLIENT_ID','DISCORD_CLIENT_SECRET','DISCORD_REDIRECT_URI',
                'DISCORD_BIND_REDIRECT_URI','SHOPIFY_API_KEY','SHOPIFY_API_SECRET','SHOPIFY_APP_KEY',
                'SHOPIFY_SHOP_URL','EMAIL_METHOD','EMAIL_CODE_EXPIRE','EMAIL_BACKEND','SENDGRID_API_KEY',
                'MAILGUN_API_KEY','MAILGUN_SENDER_DOMAIN','SUPPORT_TWITTER','SUPPORT_DISCORD',
                'INVITE_LEVEL_POINTS_PER_USER','BILLING_RATE','LEVEL_POINTS_TO_UPGRADE','LEVEL_POINTS_DECAY_RATE',
                'LEVEL_POINTS_DECAY_DAY','MIN_LEVEL','MAX_LEVEL','LEVEL_DISCOUNT_RATE','INVITE_REBATE_RATE']
    
    new_value = [discord_cliend_id,discord_secret,discord_redirect_url,
                discord_bind_redirect_url,api_key,api_scert,app_password,
                shop_url,email_method,email_code_expire,email_backend,sendgrid_api_key,
                mailgun_api_key,mailgun_sender_domain,twitter,discord,
                invite_level_points_per_user,billing_rate,level_points_to_upgrade,
                level_points_decay_rate,level_points_decay_day,min_level, max_level,
                    level_discount_rate,invite_rebate_rate ]
    data = ""
    with open(file, "r", encoding="utf-8") as f1:
        data = f1.readlines()
        for i in range(len(settings_var)):
            for line in range(len(data)):
                if settings_var[i]+'=' in data[line] and isinstance(new_value[i],str):
                    data[line] = settings_var[i] + "='" + new_value[i] + "'\n"
                elif settings_var[i]+'=' in data[line] and isinstance(new_value[i],int):
                    data[line] = settings_var[i] + "=" + str(new_value[i]) + "\n"
                elif settings_var[i]+'=' in data[line] and isinstance(new_value[i],float):
                    data[line] = settings_var[i] + "=" + str(new_value[i]) + "\n"
    with open(file, "w", encoding="utf-8") as f2:
        [f2.write(item) for item in data]

def get_site_setting():
    data ={
        'discord_cliend_id':settings.DISCORD_CLIENT_ID,
        'discord_secret':settings.DISCORD_CLIENT_SECRET,
        'discord_redirect_url':settings.DISCORD_REDIRECT_URI,
        'discord_bind_redirect_url':settings.DISCORD_BIND_REDIRECT_URI,
        'api_key':settings.SHOPIFY_API_KEY,
        'api_scert':settings.SHOPIFY_API_SECRET,
        'app_password':settings.SHOPIFY_APP_KEY,
        'shop_url':settings.SHOPIFY_SHOP_URL,
        'email_method':settings.EMAIL_METHOD,
        'email_code_expire':settings.EMAIL_CODE_EXPIRE,
        'email_backend':settings.EMAIL_BACKEND,
        'sendgrid_api_key':settings.SENDGRID_API_KEY,
        'mailgun_api_key':settings.MAILGUN_API_KEY,
        'mailgun_sender_domain':settings.MAILGUN_SENDER_DOMAIN, 
        'twitter':settings.SUPPORT_TWITTER,
        'discord':settings.SUPPORT_DISCORD,
        'invite_level_points_per_user':settings.INVITE_LEVEL_POINTS_PER_USER,
        'level_points_to_upgrade':settings.LEVEL_POINTS_TO_UPGRADE,
        'level_points_decay_rate':settings.LEVEL_POINTS_DECAY_RATE,
        'level_points_decay_day':settings.LEVEL_POINTS_DECAY_DAY,
        'min_level' :settings.MIN_LEVEL,
        'max_level':settings.MAX_LEVEL,
        'level_discount_rate':settings.LEVEL_DISCOUNT_RATE,
        'invite_rebate_rate':settings.INVITE_REBATE_RATE
    }
    return data