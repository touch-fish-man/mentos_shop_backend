
def save_site_settings(file,settings_var, new_value):
    """
    保存网站设置
    """

    data = ""
    with open(file, "r", encoding="utf-8") as f1:
        data = f1.readlines()
        for i in range(len(settings_var)):
            for line in range(len(data)):
                if settings_var[i]+'=' in data[line]:
                    data[line] = settings_var[i] + "=" + new_value[i] + '\n'
    with open(file, "w", encoding="utf-8") as f2:
        [f2.write(item) for item in data]

                