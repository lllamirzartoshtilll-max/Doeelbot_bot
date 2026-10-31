import json
import os
import random
import time
import urllib.request

TOKEN = '...'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN
USERS_FILE = 'users_data_v3.json'

CHANNEL_1 = '@toyetazad'
CHANNEL_2 = '@poshitibani'


def load_data():
  if os.path.exists(USERS_FILE):
    try:
      with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
    except:
      return {}
  return {}


def save_data(data):
  with open(USERS_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


users_db = load_data()


def get_updates(offset=None):
  url = BASE_URL + '/getUpdates?timeout=30'
  if offset:
    url = url + '&offset=' + str(offset)
  try:
    response = urllib.request.urlopen(url, timeout=35)
    data = json.loads(response.read().decode('utf-8'))
    if data.get('ok'):
      return data['result']
  except Exception as e:
    print('خطای موقت شبکه:', e)
  return []


def send_message(chat_id, text, reply_markup=None):
  url = BASE_URL + '/sendMessage'
  data_dict = {'chat_id': chat_id, 'text': text}
  if reply_markup:
    data_dict['reply_markup'] = reply_markup

  payload = json.dumps(data_dict).encode('utf-8')
  req = urllib.request.Request(
      url, data=payload, headers={'Content-Type': 'application/json'}
  )
  try:
    urllib.request.urlopen(req, timeout=10)
  except Exception as e:
    print('خطا در ارسال پیام:', e)


def answer_callback_query(callback_query_id, text=''):
  url = BASE_URL + '/answerCallbackQuery'
  data_dict = {
      'callback_query_id': callback_query_id,
      'text': text,
      'show_alert': False,
  }
  payload = json.dumps(data_dict).encode('utf-8')
  req = urllib.request.Request(
      url, data=payload, headers={'Content-Type': 'application/json'}
  )
  try:
    urllib.request.urlopen(req, timeout=5)
  except:
    pass


def check_user_membership(chat_id, channel_username):
  url = (
      f'{BASE_URL}/getChatMember?chat_id={channel_username}&user_id={chat_id}'
  )
  try:
    response = urllib.request.urlopen(url, timeout=10)
    data = json.loads(response.read().decode('utf-8'))
    if data.get('ok'):
      status = data['result'].get('status')
      if status in ['member', 'administrator', 'creator']:
        return True
  except Exception as e:
    print(f'خطا در بررسی عضویت کانال {channel_username}:', e)
  return False


def get_or_create_user(chat_id, text_start=''):
  if chat_id not in users_db:
    users_db[chat_id] = {
        'balance': 50000,
        'wins': 0,
        'losses': 0,
        'invited_count': 0,
        'referred_by': None,
        'awaiting_card': False,
        'selected_mode': 'easy',
    }
    if text_start.startswith('/start ') and len(text_start) > 7:
      ref_id = text_start.split()[1]
      if ref_id in users_db and ref_id != chat_id:
        users_db[chat_id]['referred_by'] = ref_id
        users_db[ref_id]['invited_count'] += 1

        reward = 20000 if users_db[ref_id]['balance'] == 0 else 10000
        users_db[ref_id]['balance'] += reward

        send_message(
            ref_id,
            f'🎉 یک نفر با لینک اختصاصی شما وارد ربات شد!\nمبلغ {reward:,}'
            f' تومان پاداش دعوت به موجودی شما اضافه شد.\nموجودی جدید:'
            f' {users_db[ref_id]["balance"]:,} تومان',
        )
    save_data(users_db)
  return users_db[chat_id]


print('ربات با موفقیت و سیستم ضدقطعی روشن شد...')
offset = None

while True:
  try:
    updates = get_updates(offset)
    for update in updates:
      offset = update['update_id'] + 1

      if 'message' in update:
        chat_id = str(update['message']['chat']['id'])
        text = update['message'].get('text', '')

        is_m1 = check_user_membership(chat_id, CHANNEL_1)
        is_m2 = check_user_membership(chat_id, CHANNEL_2)

        if not (is_m1 and is_m2):
          join_text = (
              '⚠️ برای استفاده از ربات و دریافت ۵۰,۰۰۰ تومان اعتبار هدیه، لطفاً'
              f' ابتدا در کانال‌های زیر عضو شوید:\n\n1️⃣ {CHANNEL_1}\n2️⃣'
              f' {CHANNEL_2}\n\nسپس روی دکمه «✅ عضو شدم، تأیید و ورود» کلیک'
              ' کنید.'
          )
          keyboard = {
              'inline_keyboard': [
                  [
                      {
                          'text': '📢 کانال اول',
                          'url': 'https://t.me/toyetazad',
                      },
                      {
                          'text': '📢 کانال دوم',
                          'url': 'https://t.me/poshitibani',
                      },
                  ],
                  [
                      {
                          'text': '✅ عضو شدم، تأیید و ورود',
                          'callback_data': 'check_join',
                      }
                  ],
              ]
          }
          send_message(chat_id, join_text, reply_markup=keyboard)
          continue

        user = get_or_create_user(chat_id, text)

        if user.get('awaiting_card'):
          user['card_number'] = text
          user['awaiting_card'] = False
          save_data(users_db)
          send_message(
              chat_id,
              f'✅ شماره کارت ({text}) با موفقیت ثبت شد!\nمبلغ درخواستی پس از'
              ' کسر ۱۰ درصد کارمزد به زودی به حساب شما واریز خواهد شد.',
          )
          continue

        if text.startswith('/start') or text:
          welcome_text = (
              'سلام! خوش آمدید به ربات دوئل سنگ، کاغذ، قیچی 🎮\n\nحساب شما فعال'
              ' شد و ۵۰,۰۰۰ تومان اعتبار هدیه دارید!\nاز منوی زیر استفاده کنید:'
          )
          keyboard = {
              'inline_keyboard': [
                  [
                      {'text': '🎮 شروع بازی', 'callback_data': 'play_menu'},
                      {
                          'text': '💰 حساب من و برداشت',
                          'callback_data': 'wallet',
                      },
                  ],
                  [
                      {
                          'text': '👥 دریافت لینک دعوت اختصاصی',
                          'callback_data': 'ref_link',
                      }
                  ],
              ]
          }
          send_message(chat_id, welcome_text, reply_markup=keyboard)

      elif 'callback_query' in update:
        query = update['callback_query']
        query_id = query['id']
        chat_id = str(query['message']['chat']['id'])
        data = query['data']

        answer_callback_query(query_id)

        is_m1 = check_user_membership(chat_id, CHANNEL_1)
        is_m2 = check_user_membership(chat_id, CHANNEL_2)

        if not (is_m1 and is_m2) and data != 'check_join':
          send_message(
              chat_id,
              '⚠️ شما هنوز در کانال‌ها عضو نیستید! لطفاً ابتدا عضو شوید.',
          )
          continue

        user = get_or_create_user(chat_id)

        if data == 'check_join':
          if is_m1 and is_m2:
            answer_callback_query(query_id, '✅ عضویت شما تایید شد!')
            welcome_text = (
                '🎉 تبریک! عضویت شما تایید شد.\n\nخوش آمدید به ربات دوئل سنگ،'
                ' کاغذ، قیچی 🎮\nاز منوی زیر استفاده کنید:'
            )
            keyboard = {
                'inline_keyboard': [
                    [
                        {'text': '🎮 شروع بازی', 'callback_data': 'play_menu'},
                        {
                            'text': '💰 حساب من و برداشت',
                            'callback_data': 'wallet',
                        },
                    ],
                    [
                        {
                            'text': '👥 دریافت لینک دعوت اختصاصی',
                            'callback_data': 'ref_link',
                        }
                    ],
                ]
            }
            send_message(chat_id, welcome_text, reply_markup=keyboard)
          else:
            answer_callback_query(
                query_id, '❌ هنوز در همه کانال‌ها عضو نشده‌اید!'
            )

        elif data == 'play_menu':
          keyboard = {
              'inline_keyboard': [
                  [
                      {
                          'text': '🟢 آسان (۱۰,۰۰۰ تومان)',
                          'callback_data': 'mode_easy',
                      }
                  ],
                  [
                      {
                          'text': '🟡 متوسط (۵۰,۰۰۰ تومان)',
                          'callback_data': 'mode_medium',
                      }
                  ],
                  [
                      {
                          'text': '🔴 سخت (۱۰۰,۰۰۰ تومان)',
                          'callback_data': 'mode_hard',
                      }
                  ],
                  [
                      {
                          'text': '🔙 بازگشت به منوی اصلی',
                          'callback_data': 'back_home',
                      }
                  ],
              ]
          }
          send_message(
              chat_id,
              'لطفاً سطح دوئل خود را انتخاب کنید:',
              reply_markup=keyboard,
          )

        elif data.startswith('mode_'):
          mode_map = {
              'mode_easy': 'easy',
              'mode_medium': 'medium',
              'mode_hard': 'hard',
          }
          user['selected_mode'] = mode_map[data]
          save_data(users_db)

          amounts = {
              'easy': '۱۰,۰۰۰ تومان',
              'medium': '۵۰,۰۰۰ تومان',
              'hard': '۱۰۰,۰۰۰ تومان',
          }
          current_amount = amounts[user['selected_mode']]

          keyboard = {
              'inline_keyboard': [
                  [
                      {'text': '🪨 سنگ', 'callback_data': 'rock'},
                      {'text': '📄 کاغذ', 'callback_data': 'paper'},
                      {'text': '✂️ قیچی', 'callback_data': 'scissors'},
                  ],
                  [
                      {
                          'text': '🔙 انتخاب سطح دیگر',
                          'callback_data': 'play_menu',
                      }
                  ],
              ]
          }
          send_message(
              chat_id,
              f'سطح انتخابی: {current_amount}\nحال انتخاب خود را انجام دهید:',
              reply_markup=keyboard,
          )

        elif data == 'back_home':
          keyboard = {
              'inline_keyboard': [
                  [
                      {'text': '🎮 شروع بازی', 'callback_data': 'play_menu'},
                      {
                          'text': '💰 حساب من و برداشت',
                          'callback_data': 'wallet',
                      },
                  ],
                  [
                      {
                          'text': '👥 دریافت لینک دعوت اختصاصی',
                          'callback_data': 'ref_link',
                      }
                  ],
              ]
          }
          send_message(chat_id, 'منوی اصلی ربات:', reply_markup=keyboard)

        elif data == 'wallet':
          wallet_text = (
              f'💰 کیف پول شما:\n\nموجودی: {user["balance"]:,} تومان\n🏆'
              f' بردها: {user["wins"]}\n❌ باخت‌ها: {user["losses"]}\n👥 دوستان'
              f' دعوت‌شده: {user["invited_count"]} / ۵ نفر\n\n⚠️ کارمزد ما از هر'
              ' برداشت شما ۱۰ درصده\n\n-------------------\nشرط برداشت: رسیدن'
              ' به ۱,۰۰۰,۰۰۰ تومان و دعوت حداقل ۵ نفر.'
          )
          keyboard = {
              'inline_keyboard': [
                  [
                      {
                          'text': '🎁 درخواست برداشت وجه',
                          'callback_data': 'withdraw',
                      }
                  ],
                  [
                      {
                          'text': '👥 دریافت لینک دعوت اختصاصی',
                          'callback_data': 'ref_link',
                      }
                  ],
                  [
                      {
                          'text': '🔙 بازگشت به منوی اصلی',
                          'callback_data': 'back_home',
                      }
                  ],
              ]
          }
          send_message(chat_id, wallet_text, reply_markup=keyboard)

        elif data == 'ref_link':
          bot_username = 'Doeelbot'
          ref_url = f'https://t.me/{bot_username}?start={chat_id}'
          ref_text = (
              '👥 **سیستم دعوت دوستان و کسب درآمد:**\n\nبا لینک اختصاصی زیر'
              ' دوستان خود را دعوت کنید:\n🔹 اگر موجودی شما بیشتر از صفر باشد:'
              ' **۱۰,۰۰۰ تومان** پاداش\n🔹 اگر موجودی شما **صفر** باشد: **۲۰,۰۰۰'
              f' تومان** جایزه به ازای هر نفر!\n\nتعداد دعوت‌های شما:'
              f' {user["invited_count"]} / ۵\n\n🔗 لینک اختصاصی'
              f' شما:\n`{ref_url}`\n\n*(روی لینک بالا بزنید تا کپی شود و آن را'
              ' برای دوستانتان بفرستید)*\n\n⚠️ کارمزد ما از هر برداشت شما ۱۰'
              ' درصده'
          )
          keyboard = {
              'inline_keyboard': [
                  [
                      {
                          'text': '🔙 بازگشت به منوی اصلی',
                          'callback_data': 'back_home',
                      }
                  ]
              ]
          }
          send_message(chat_id, ref_text, reply_markup=keyboard)

        elif data == 'withdraw':
          if user['balance'] >= 1000000 and user['invited_count'] >= 5:
            user['awaiting_card'] = True
            save_data(users_db)
            send_message(
                chat_id,
                '🎉 شرایط برداشت شما تکمیل است!\nلطفاً شماره کارت بانکی خود را'
                ' (به نام خودتان) در قالب یک پیام متنی بفرستید تا ثبت شود.',
            )
          else:
            b_needed = max(0, 1000000 - user['balance'])
            i_needed = max(0, 5 - user['invited_count'])
            send_message(
                chat_id,
                f'⚠️ هنوز به شرایط برداشت نرسیدید!\n\nموجودی لازم: ۱,۰۰۰,۰۰۰'
                f' تومان (کسری: {b_needed:,} تومان)\nتعداد دعوت لازم: ۵ نفر'
                f' (کمبود: {i_needed} نفر)\n\n⚠️ کارمزد ما از هر برداشت شما ۱۰'
                ' درصده',
            )

        elif data in ['rock', 'paper', 'scissors']:
          user_choice = data
          choices = ['rock', 'paper', 'scissors']
          bot_choice = random.choice(choices)

          names = {'rock': '🪨 سنگ', 'paper': '📄 کاغذ', 'scissors': '✂️ قیچی'}

          mode = user.get('selected_mode', 'easy')
          stakes = {'easy': 10000, 'medium': 50000, 'hard': 100000}
          stake_amount = stakes[mode]

          if user['balance'] < stake_amount:
            bot_username = 'Doeelbot'
            ref_url = f'https://t.me/{bot_username}?start={chat_id}'
            out_text = (
                f'⚠️ موجودی شما ({user["balance"]:,} تومان) برای شرکت در این دوئل'
                ' کافی نیست!\n\nموجودی شما تمام شد! برای دریافت **۲۰,۰۰۰ تومان'
                ' جایزه** به ازای هر دعوت، از لینک اختصاصی زیر استفاده کنید و'
                f' دوستان خود را دعوت کنید:\n\n`{ref_url}`'
            )
            keyboard = {
                'inline_keyboard': [
                    [
                        {
                            'text': '👥 دریافت لینک دعوت اختصاصی',
                            'callback_data': 'ref_link',
                        }
                    ],
                    [
                        {
                            'text': '🔙 بازگشت به منوی اصلی',
                            'callback_data': 'back_home',
                        }
                    ],
                ]
            }
            send_message(chat_id, out_text, reply_markup=keyboard)
            continue

          if user_choice == bot_choice:
            result_text = 'نتیجه: مساوی شدید! (بدون تغییر در موجودی) 😐'
          elif (
              (user_choice == 'rock' and bot_choice == 'scissors')
              or (user_choice == 'paper' and bot_choice == 'rock')
              or (user_choice == 'scissors' and bot_choice == 'paper')
          ):
            user['wins'] += 1
            user['balance'] += stake_amount
            result_text = f'نتیجه: برنده شدید! 🎉 (+{stake_amount:,} تومان)'
          else:
            user['losses'] += 1
            user['balance'] = max(0, user['balance'] - stake_amount)
            result_text = f'نتیجه: باختید! 🤖 (-{stake_amount:,} تومان)'

          save_data(users_db)

          reply_text = (
              f'سطح بازی: {mode.upper()}\nانتخاب شما: {names[user_choice]}\nانتخاب'
              f' ربات: {names[bot_choice]}\n\n{result_text}\n\nموجودی فعلی:'
              f' {user["balance"]:,} تومان\n\n⚠️ کارمزد ما از هر برداشت شما ۱۰'
              ' درصده'
          )
          keyboard = {
              'inline_keyboard': [
                  [
                      {'text': '🎮 بازی مجدد', 'callback_data': 'play_menu'},
                      {'text': '💰 کیف پول', 'callback_data': 'wallet'},
                  ],
                  [
                      {
                          'text': '👥 لینک دعوت اختصاصی',
                          'callback_data': 'ref_link',
                      }
                  ],
              ]
          }
          send_message(chat_id, reply_text, reply_markup=keyboard)

  except Exception as e:
    print('خطای کلی در حلقه ربات:', e)

  time.sleep(1)
    
