import click
import os


@click.group()
def cli():
    pass


def update_dist():
    """
    更新前端重新部署
    """
    os.system("rm -rf /opt/mentos_shop_backend/dist/*")
    os.system("wget  https://zlp-1251420975.cos.accelerate.myqcloud.com/vue/dist.zip -O /tmp/dist.zip")
    os.system("unzip /tmp/dist.zip -d /opt/mentos_shop_backend/dist/")
    os.system("rm -rf /tmp/dist.zip")


@cli.command()
def update_frontend():
    """
    更新前端
    """
    update_dist()
    print("前端更新完成")


@cli.command()
def update_backend():
    """
    更新后端
    """
    os.system("docker exec -it mentos mentos_cli update")


@cli.command()
def maintain():
    """
    维护模式 开/关 docker外执行
    """
    if os.path.exists("/opt/mentos_shop_backend/dist/maintain"):
        update_dist()
        print("维护模式已关闭")
    else:
        os.system("rm -rf /opt/mentos_shop_backend/dist/*")
        os.system("cp -r /opt/mentos_shop_backend/config/nginx/html/maintain/* /opt/mentos_shop_backend/dist/")
        print("维护模式已开启")


def install_docker():
    """
    ubuntu安装docker
    """
    os.system("curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun")
    os.system("systemctl enable docker")
    os.system("systemctl start docker")
    print("docker安装完成")


def install_docker_compose():
    """
    安装docker-compose
    """
    os.system(
        'sudo curl -L "https://github.com/docker/compose/releases/download/2.22.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose')
    os.system("chmod +x /usr/local/bin/docker-compose")
    print("docker-compose安装完成")


@cli.command()
def init():
    """
    安装docker和docker-compose
    """
    install_docker()
    install_docker_compose()


@cli.command()
def install():
    """
    部署项目
    """
    os.system("git pull")
    os.system("cp -r config/* /opt/mentos_shop_backend/config/")
    os.system("cp -r src/* /opt/mentos_shop_backend/src/")
    update_dist()
    os.system("docker-compose build --no-cache")
    os.system("docker-compose down")
    os.system("docker-compose up -d")
    print("部署完成")


@cli.command()
@click.argument('action')
def mentos_cli(action='help'):
    """
    mentos_cli
    """
    os.system("docker exec -it mentos mentos_cli {}".format(action))


cli_all = click.CommandCollection(sources=[cli])
if __name__ == '__main__':
    cli_all()
