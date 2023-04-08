import random
import string

from faker import Faker
import os
import sys

from init_env import *

from apps.tickets.models import Question
from rich.console import Console

console = Console()

fake = Faker(locale='zh_CN')
def main():
    with console.status("[bold green]Generating faq...") as status:
        Question.objects.all().delete()
        print("Generating faq...")
        for i in range(50):
            question = fake.sentence()
            answer = fake.text()
            Question.objects.create(question=question, answer=answer)

if __name__ == '__main__':
    main()