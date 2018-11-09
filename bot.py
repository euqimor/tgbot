import yaml
import logging
import requests
from time import time
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from telegram import InlineQueryResultPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from os import environ


def write_on_image(image: BytesIO, line: list):
    text = ' '.join(line)
    img = Image.open(image)
    fnt = ImageFont.truetype('comic.ttf', 50)
    d = ImageDraw.Draw(img)
    w, h = d.textsize(text, font=fnt)

    def write_one_line(line, text_x, text_y):
        text = ' '.join(line)
        # creating black outline
        d.text((text_x - 1, text_y), text, font=fnt, fill='black')
        d.text((text_x + 1, text_y), text, font=fnt, fill='black')
        d.text((text_x, text_y - 1), text, font=fnt, fill='black')
        d.text((text_x, text_y + 1), text, font=fnt, fill='black')
        # end creating outline
        d.text((text_x, text_y), text, font=fnt)
    if w//img.width > 0:
        for word in line: # checking if there's a single word larger than image width
            if d.textsize(word, font=fnt)[0] >= img.width:
                image.seek(0)
                return image
        lines = []
        single_line = ''
        remaining_text = text.split(' ')
        while remaining_text:
            word = remaining_text.pop(0)
            single_line_future = single_line+' '+word
            if not remaining_text and d.textsize(single_line_future, font=fnt)[0] < img.width:
                lines.append(single_line_future.strip())
            elif d.textsize(single_line_future, font=fnt)[0] > img.width:
                lines.append(single_line.strip())
                single_line = ''
                remaining_text.insert(0, word)
            else:
                single_line = single_line_future
            # if not remaining_text or d.textsize(single_line_future, font=fnt)[0] > img.width:
            #     lines.append(single_line.strip())
            #     single_line = word
            # else:
            #     single_line = single_line_future
        adjust_y = 0
        for line in lines:
            w, h = d.textsize(line, font=fnt)
            text_x = img.width // 2 - w / 2
            text_y = img.height * 2 // 3 - h / 2 + adjust_y
            adjust_y += 2*h/3
            write_one_line(line.split(' '), text_x, text_y)
    else:
        text_x = img.width // 2 - w / 2
        text_y = img.height * 2 // 3 - h / 2
        write_one_line(line, text_x, text_y)
        # # creating black outline
        # d.text((text_x-1, text_y), text, font=fnt, fill='black')
        # d.text((text_x+1, text_y), text, font=fnt, fill='black')
        # d.text((text_x, text_y-1), text, font=fnt, fill='black')
        # d.text((text_x, text_y+1), text, font=fnt, fill='black')
        # # end creating outline
        # d.text((text_x, text_y), text, font=fnt)
    image.seek(0)
    img = img.convert('RGB')
    img.save(image, format='jpeg')
    image.seek(0)
    return image


def resize_image(image: BytesIO, basewidth):
    img = Image.open(image)
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    image.seek(0)
    img.save(image, format='jpeg')
    image.seek(0)
    return image


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Привет! Эта тема ничего не делает, лучше попробуй /котик :3")


def inline_cats(bot, update):
    if environment_type == 'prod':
        return
    query = update.inline_query.query
    if not query:
        return
    elif query == 'котики':
        results = list()
        results.append(
            InlineQueryResultPhoto(
                id='cat',
                title='Котик',
                photo_url='https://cataas.com/c',
                thumb_url='https://cataas.com/c'
            )
        )
        bot.answer_inline_query(update.inline_query.id, results)


def cat(bot, update, args):
    photo = BytesIO(requests.get('https://cataas.com/c').content)
    if args and args[0].lower() == 'говорит':
        args.pop(0)
        photo_with_text = write_on_image(photo, args)
        bot.send_photo(chat_id=update.message.chat_id, photo=photo_with_text)
    else:
        bot.send_photo(chat_id=update.message.chat_id, photo=photo)


def dog(bot, update, args):
    dog_url = requests.get('https://dog.ceo/api/breeds/image/random').json()['message']
    if args and args[0].lower() == 'говорит':
        args.pop(0)
        photo = BytesIO(requests.get(dog_url).content)
        photo = resize_image(photo, 600)
        photo_with_text = write_on_image(photo, args)
        bot.send_photo(chat_id=update.message.chat_id, photo=photo_with_text)
    else:
        bot.send_photo(chat_id=update.message.chat_id, photo=dog_url)


def adik(bot, update):
    if update.message.chat_id != -185227991:
        return
    global adik_cd
    text = update.message.text
    time_used = time()
    cooldown_check = time_used - adik_cd
    if any(x in text for x in ['\\0','\\o','\\O','\\о','\\О']) and cooldown_check >= 1800:
        bot.send_photo(chat_id=update.message.chat_id, photo=adik_photo)
        adik_photo.seek(0)
        adik_cd = time_used


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    try:
        environment_type = environ['environment_type']
        if environment_type == 'prod':
            with open('settings.yml') as f:
                token = yaml.load(f)['prod']
        elif environment_type == 'test':
            with open('settings.yml') as f:
                token = yaml.load(f)['test']
    except KeyError:
        with open('settings.yml') as f:
            token = yaml.load(f)['test']

    with open('adik', 'rb') as f:
        adik_photo = BytesIO(f.read())

    adik_cd = 0.0
    updater = Updater(token=token)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    adik_handler = MessageHandler(Filters.text, adik)
    cats_handler = CommandHandler(['котик', 'кот', 'cat', 'ket'], cat, pass_args=True)
    dogs_handler = CommandHandler(['пёсик', 'пёсель', 'песик', 'песель', 'пёс', 'пес', 'dog', 'doggo'], dog, pass_args=True)
    inline_cats_handler = InlineQueryHandler(inline_cats)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(adik_handler)
    dispatcher.add_handler(cats_handler)
    dispatcher.add_handler(dogs_handler)
    dispatcher.add_handler(inline_cats_handler)

    updater.start_polling()
