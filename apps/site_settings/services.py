from django.conf import settings
from config.env import env

def change_site_settings():
    revoke_dict = {
        'discord_client_id':settings.DISCORD_CLIENT_ID,
        'discord_client_secret':settings.DISCORD_CLIENT_SECRET,
        'discord_redirect_uri':settings.DISCORD_REDIRECT_URI,
        'discord_bind_redirect_uri':settings.DISCORD_BIND_REDIRECT_URI,

        'shopify_api_key':settings.SHOPIFY_API_KEY,
        'shopify_api_secret':settings.SHOPIFY_API_SECRET,
        'shopify_app_key':settings.SHOPIFY_APP_KEY,
        'shopify_shop_url':settings.SHOPIFY_SHOP_URL,

        'email_method':settings.EMAIL_METHOD,
        'email_code_expire':settings.EMAIL_CODE_EXPIRE,
        'sendgrid_api_key':settings.SENDGRID_API_KEY,
        'mailgun_api_key':settings.MAILGUN_API_KEY,
        'mailgun_sender_domain':settings.MAILGUN_SENDER_DOMAIN, 

        'support_twitter':settings.SUPPORT_TWITTER,
        'support_discord':settings.SUPPORT_DISCORD,
        'invite_level_points_per_user':settings.INVITE_LEVEL_POINTS_PER_USER,
        'billing_rate':settings.BILLING_RATE,
        'level_points_decay_rate':settings.LEVEL_POINTS_DECAY_RATE,
        'level_points_decay_day':settings.LEVEL_POINTS_DECAY_DAY,
        'min_level' :settings.MIN_LEVEL,
        'max_level':settings.MAX_LEVEL,
        'level_discount_rate':settings.LEVEL_DISCOUNT_RATE,
        'invite_rebate_rate':settings.INVITE_REBATE_RATE
    }
    try:
        settings.DISCORD_CLIENT_ID = env('DISCORD_CLIENT_ID')
        settings.DISCORD_CLIENT_SECRET = env('DISCORD_CLIENT_SECRET')
        settings.DISCORD_REDIRECT_URI = env('DISCORD_REDIRECT_URI')
        settings.DISCORD_BIND_REDIRECT_URI = env('DISCORD_BIND_REDIRECT_URI')
        settings.SHOPIFY_API_KEY = env('SHOPIFY_API_KEY')
        settings.SHOPIFY_API_SECRET = env('SHOPIFY_API_SECRET')
        settings.SHOPIFY_SHOP_URL = env('SHOPIFY_SHOP_URL')
        settings.SHOPIFY_APP_KEY = env('SHOPIFY_APP_KEY')
        settings.EMAIL_METHOD = env('EMAIL_METHOD') 
        settings.EMAIL_CODE_EXPIRE = int(env('EMAIL_CODE_EXPIRE'))
        settings.SENDGRID_API_KEY = env('SENDGRID_API_KEY')
        settings.MAILGUN_API_KEY = env('MAILGUN_API_KEY')
        settings.MAILGUN_SENDER_DOMAIN = env('MAILGUN_SENDER_DOMAIN')
        settings.SUPPORT_TWITTER = env('SUPPORT_TWITTER')
        settings.SUPPORT_DISCORD = env('SUPPORT_DISCORD')
        settings.INVITE_LEVEL_POINTS_PER_USER = int(env('INVITE_LEVEL_POINTS_PER_USER')) 
        settings.BILLING_RATE = float(env('BILLING_RATE'))
        settings.LEVEL_POINTS_DECAY_RATE = float(env('LEVEL_POINTS_DECAY_RATE'))  
        settings.LEVEL_POINTS_DECAY_DAY = int(env('LEVEL_POINTS_DECAY_DAY'))  
        settings.MIN_LEVEL = int(env('MIN_LEVEL')) 
        settings.MAX_LEVEL = int(env('MAX_LEVEL')) 
        settings.LEVEL_DISCOUNT_RATE = float(env('LEVEL_DISCOUNT_RATE')) 
        settings.INVITE_REBATE_RATE = float(env('INVITE_REBATE_RATE'))
        return {}
    except:
        return revoke_dict



def save_site_settings(data,file):
    """
    保存网站设置
    """
    request_data = {}
    int_var = ['EMAIL_CODE_EXPIRE','INVITE_LEVEL_POINTS_PER_USER',
               'LEVEL_POINTS_TO_UPGRADE','LEVEL_POINTS_DECAY_DAY','MIN_LEVEL','MAX_LEVEL',"POINTS_PER_MESSAGE","MAX_POINTS_PER_DAY"]
    float_var = ['BILLING_RATE','LEVEL_POINTS_DECAY_RATE','LEVEL_DISCOUNT_RATE','INVITE_REBATE_RATE']
    for key,_ in data.items():
        key_upper = key.upper()
        env.ENVIRON[key_upper] = str(data.get(key))
        if key_upper not in int_var and key_upper not in float_var:
            request_data[key_upper] = "'" +str(data.get(key))+"'"
        else:
            request_data[key_upper] = data.get(key)
    with open(file, "r", encoding="utf-8") as f1:
        data = f1.readlines()
        for key,value in request_data.items():
            for line in range(len(data)):
                if key+'=' in data[line]:
                    data[line] = '{}={}\n'.format(key,value) 

    with open(file, "w", encoding="utf-8") as f2:
        [f2.write(item) for item in data]
    

def get_site_setting():
    data ={
        'discord_client_id':settings.DISCORD_CLIENT_ID,
        'discord_client_secret':settings.DISCORD_CLIENT_SECRET,
        'discord_redirect_uri':settings.DISCORD_REDIRECT_URI,
        'discord_bind_redirect_uri':settings.DISCORD_BIND_REDIRECT_URI,
        'shopify_api_key':settings.SHOPIFY_API_KEY,
        'shopify_api_secret':settings.SHOPIFY_API_SECRET,
        'shopify_app_key':settings.SHOPIFY_APP_KEY,
        'shopify_shop_url':settings.SHOPIFY_SHOP_URL,
        'email_method':settings.EMAIL_METHOD,
        'email_code_expire':settings.EMAIL_CODE_EXPIRE,
        'sendgrid_api_key':settings.SENDGRID_API_KEY,
        'mailgun_api_key':settings.MAILGUN_API_KEY,
        'mailgun_sender_domain':settings.MAILGUN_SENDER_DOMAIN, 
        'support_twitter':settings.SUPPORT_TWITTER,
        'support_discord':settings.SUPPORT_DISCORD,
        'invite_level_points_per_user':settings.INVITE_LEVEL_POINTS_PER_USER,
        'billing_rate':settings.BILLING_RATE,
        'level_points_decay_rate':settings.LEVEL_POINTS_DECAY_RATE,
        'level_points_decay_day':settings.LEVEL_POINTS_DECAY_DAY,
        'min_level' :settings.MIN_LEVEL,
        'max_level':settings.MAX_LEVEL,
        'level_discount_rate':settings.LEVEL_DISCOUNT_RATE,
        'invite_rebate_rate':settings.INVITE_REBATE_RATE,
        'discord_bot_token':settings.DISCORD_BOT_TOKEN,
        'discord_bot_channels':settings.DISCORD_BOT_CHANNELS,
        'discord_bot_points_per_message':settings.POINTS_PER_MESSAGE,
        'discord_bot_max_points_per_day':settings.MAX_POINTS_PER_DAY,
    }
    return data