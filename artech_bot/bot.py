import os
import django
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
    CallbackQueryHandler,
)
# from dotenv import load_dotenv
from asgiref.sync import sync_to_async
from pytz import timezone
import tiktoken
import re # for processing persian names

persian_pattern = re.compile(r'^[\u0600-\u06FF\s]+$')


# Set up Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "artech_bot.settings"
)  # Replace with your project name
django.setup()

# Import the Django model after Django setup
from openai_handler import get_openai_response, openai_image_handler, openai_generate_image # Import the OpenAI-related functions from the new file
from admin_panel.models import user_data, Chat, SaleEvent, SaleClaim
from admin_panel.utils import get_bot_text
from django.db import transaction
from checkout.models import invoices, token_price, UserTokenPlan
from django.db import close_old_connections
from datetime import datetime, timedelta
from django.utils import timezone as tzSale
from django.conf import settings

# Load environment variables
# load_dotenv()

IMAGE_SAVE_PATH = os.path.join(settings.MEDIA_ROOT, "images")

async def start(update: Update, context: CallbackContext):
    close_old_connections()

    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or ""
    last_name = update.effective_user.last_name or ""
    username = update.effective_user.username or ""
    default_token = await get_bot_text(key="free_token",default="0")

    try:
        user = await user_data.objects.aget(id=user_id)
        welcome_text = await get_bot_text(key="welcome")
    except user_data.DoesNotExist:
        new_user = user_data(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            number=0,
        )
        await new_user.asave()
        welcome_text = "سلام، به بات آرتک خوش آمدید، ما اینجا هستیم تا در روند استفاده از هوش مصنوعی به شما کمک کنیم، با استفاده از امکانات این بات می توانید پرامپت های مخصوص ساخت عکس با هر هوش مصنوعی را دریافت کنید، بعلاوه می توانید سوالات خود از هر حوزه ای و موضوعی را بپرسید تا به سادگی به جواب برسید."
        print(f"[record--status:successful] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info:new user added to bot, id: {user_id}")

    keyboard = [[InlineKeyboardButton("نمایش منو", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"{welcome_text}",
        reply_markup=reply_markup,
    )
async def main_menu_handler(update: Update, context: CallbackContext):
    close_old_connections()
    query = update.callback_query
    
    # Make sure to acknowledge the callback
    if query:
        await query.answer()
        keyboard = [
            [InlineKeyboardButton("ویرایش اطلاعات کاربری", callback_data="sign_in")],
            [InlineKeyboardButton("نمایش اعتبار", callback_data="show_balance"),
            InlineKeyboardButton("خرید اعتبار", callback_data="buy_tokens")],
            [InlineKeyboardButton("توکن رایگان", callback_data="freetoken")],
            [InlineKeyboardButton("چت با کاملترین نسخه chatgpt 4.0", callback_data="change_model_gpt_4")],
            [InlineKeyboardButton("چت با نسخه chatgpt 3.5", callback_data="change_model_gpt_3")],
            [InlineKeyboardButton("تغییر مدل هوش مصنوعی", callback_data="show_model")],
            [InlineKeyboardButton("تغییر نوع پرامپت", callback_data="change_prompt")],
            [InlineKeyboardButton("راهنما", callback_data="help"),
            InlineKeyboardButton("قوانین", callback_data="policy")],
            [InlineKeyboardButton("تماس با ما", callback_data="contact_us")],
            
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        main_menu_text = await get_bot_text("main_menu")
        await query.edit_message_text(text=main_menu_text, reply_markup=reply_markup)
    else:
        # Handle when called as a command
        keyboard = [
            [InlineKeyboardButton("ویرایش اطلاعات کاربری", callback_data="sign_in")],
            [InlineKeyboardButton("نمایش اعتبار", callback_data="show_balance"),
            InlineKeyboardButton("خرید اعتبار", callback_data="buy_tokens")],
            [InlineKeyboardButton("توکن رایگان", callback_data="freetoken")],
            [InlineKeyboardButton("چت با کاملترین نسخه chatgpt 4.0", callback_data="change_model_gpt_4")],
            [InlineKeyboardButton("چت با نسخه chatgpt 3.5", callback_data="change_model_gpt_3")],
            [InlineKeyboardButton("تغییر مدل هوش مصنوعی", callback_data="show_model")],
            [InlineKeyboardButton("تغییر نوع پرامپت", callback_data="change_prompt")],
            [InlineKeyboardButton("راهنما", callback_data="help"),
            InlineKeyboardButton("قوانین", callback_data="policy")],
            [InlineKeyboardButton("تماس با ما", callback_data="contact_us")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        main_menu_text = await get_bot_text("main_menu")
        await update.message.reply_text(text=main_menu_text, reply_markup=reply_markup)


async def sign_in_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id

    if query:
        await query.answer()
        
        if not context.user_data.get('user'):
            try:
                user = await user_data.objects.aget(id=user_id)
            except user_data.DoesNotExist:
                user = user_data(id=user_id, first_name=None, number=None)
                await user.asave()
            context.user_data['user'] = user
            
        user = context.user_data['user']

        if query.data == "sign_in":
            if user.first_name and user.number:
                # Show existing info with verify/edit buttons
                keyboard = [
                    [InlineKeyboardButton("تایید", callback_data="verify")],
                    [InlineKeyboardButton("ویرایش", callback_data="edit")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"اطلاعات فعلی شما:\nنام: {user.first_name}\nشماره: {user.number}\n\nآیا میخواهید تغییر دهید؟",
                    reply_markup=reply_markup
                )
            else:
                # Ask for name if missing info
                context.user_data['awaiting_name'] = True
                await query.edit_message_text("لطفا نام خود را وارد کنید:")
            return

        elif query.data == "verify":
            context.user_data['awaiting_name'] = False
            context.user_data['awaiting_number'] = False
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"اطلاعات شما با موفقیت ثبت شد.\nنام: {user.first_name}\nشماره: {user.number}",
                reply_markup=reply_markup
            )
            return

        elif query.data == "edit":
            keyboard = [
                [InlineKeyboardButton("ویرایش نام", callback_data="edit_name")],
                [InlineKeyboardButton("ویرایش شماره", callback_data="edit_number")],
                [InlineKeyboardButton("بازگشت", callback_data="sign_in")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "کدام مورد را میخواهید ویرایش کنید؟",
                reply_markup=reply_markup
            )
            return
            
        elif query.data == "edit_name":
            context.user_data['awaiting_name'] = True
            await query.edit_message_text("لطفا نام جدید خود را وارد کنید:")
            return
            
        elif query.data == "edit_number":
            context.user_data['awaiting_number'] = True
            await query.edit_message_text("لطفا شماره جدید خود را وارد کنید:")
            return
        elif query.data == "main_menu":
            await start(update, context)
            return

async def handle_texts(update: Update, context: CallbackContext):
    # First check if we're awaiting name or number input
    if context.user_data.get('awaiting_name'):
        new_name = update.message.text
        if not persian_pattern.fullmatch(new_name):
            await update.message.reply_text("لطفاً تنها از حروف فارسی استفاده کنید.")
            return  
        user = context.user_data['user']
        user.first_name = new_name
        await user.asave()

        # Check if user already has a number
        if user.number:
            keyboard = [
                [InlineKeyboardButton("تایید", callback_data="verify")],
                [InlineKeyboardButton("ویرایش", callback_data="edit")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"نام شما به {new_name} ثبت شد.",
                reply_markup=reply_markup
            )
        else:
            # Only ask for number if user doesn't have one
            await update.message.reply_text(f"نام شما به {new_name} ثبت شد.\nلطفا شماره تماس خود را وارد کنید:")
            context.user_data['awaiting_number'] = True
        
        context.user_data['awaiting_name'] = False
        return

    elif context.user_data.get('awaiting_number'):
        new_number = update.message.text
        if new_number.isdigit() and 10<=len(new_number)<=11: # force user phone number to be 11 or 10 digits
            user = context.user_data['user']
            user.number = int(new_number)
            await user.asave()
            
            keyboard = [
                [InlineKeyboardButton("تایید", callback_data="verify")],
                [InlineKeyboardButton("ویرایش", callback_data="edit")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"شماره شما به {new_number} ثبت شد.",
                reply_markup=reply_markup
            )
            context.user_data['awaiting_number'] = False
        else:
            await update.message.reply_text("لطفا یک شماره معتبر وارد کنید.")
        return
# Check if we're awaiting an image generation prompt
    if context.user_data.get('awaiting_image_prompt'):
        image_prompt = update.message.text
        user_id = update.effective_user.id
        # Use sync_to_async to call the synchronous image generation function
        image_url = await sync_to_async(openai_generate_image)(user_id, image_prompt)
        context.user_data['awaiting_image_prompt'] = False
        if image_url.startswith("Error:"):
            await update.message.reply_text(f"خطا در تولید تصویر: {image_url}")
        else:
            await update.message.reply_photo(photo=image_url)
        return
    # If not awaiting input, proceed with normal message handling
    close_old_connections()
    user_id = update.effective_user.id
    user_message = update.message.text if update.message.text else "(No text)"
    user = await user_data.objects.aget(id=user_id)

    if context.user_data.get('awaiting_token_price'):
        user_input = update.message.text
        if user_input.isdigit():
            website = os.getenv("WEBSITE_URL")
            new_invoice = invoices(
                user_id = user,
                amount = int(user_input),
                status = "HOLD"
            )
            await new_invoice.asave()
            purchase_link = f"{website}/checkout/request/{new_invoice.id}"
            await update.message.reply_text(
                text=f"برای تکمیل خرید از طریق این لینک اقدام کنید: {purchase_link}"
            )
            context.user_data['awaiting_token_price'] = False
            return
        else:
            await update.message.reply_text(
                text=f"مقدار وارد شده صحیح نمیباشد دوباره تلاش کنید"
            )
            return
    if await token_handler(user, user_message):  # Check if the user has enough tokens
        response = await sync_to_async(get_openai_response)(user_id, user_message)

        # Save the chat data into the Chat model asynchronously
        new_chat = Chat(
            user_id=user,  # Set the ForeignKey relation to the user
            message=user_message,
            response=response,
        )
        await new_chat.asave()  # Save the chat data asynchronously

        # Reply to the user with the AI's response
        await update.message.reply_text(response)
        print(
            f"[record--status:successful] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info: massage sent to user: {user_id}"
        )
    else:
        keyboard = [[InlineKeyboardButton("خرید اعتبارf", callback_data="show_tokens")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "حجم مصرف اعتبارf های شما به پایان رسیده.",
            reply_markup=reply_markup
        )  # You don't have an active subscription

async def handle_photoes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    # Retrieve the user asynchronously
    user = await sync_to_async(user_data.objects.get)(id=user_id)
    
    # Get the largest photo from the message
    photo_file = update.message.photo[-1].file_id
    new_file = await context.bot.get_file(photo_file)
    
    # Create the directory if it doesn't exist
    if not os.path.exists(IMAGE_SAVE_PATH):
        os.makedirs(IMAGE_SAVE_PATH)
    
    # Define the file path for saving the image
    file_path = os.path.join(
        IMAGE_SAVE_PATH,
        f"{user_id}_{datetime.now(tz=timezone('asia/tehran')).strftime('%Y%m%d_%H%M%S')}.jpg"
    )
    
    # Download and save the image to the file_path
    await new_file.download_to_drive(file_path)
    print(f"[record--status:successful] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info: image saved from user: {user_id}")
    
    # Instead of checking for a subscription, check if the user has enough tokens
    # Using "image processing" as the message to determine token usage (adjust if needed)
    if await token_handler(user, "image processing"):
        # Process the image using your openai_image_handler
        response = await sync_to_async(openai_image_handler)(user_id, file_path)
        
        # Save the chat data into the Chat model asynchronously
        new_chat = Chat(
            user_id=user,  # ForeignKey relation to the user
            message='photo',
            response=response,
            media_url=file_path  # Save the file path as the media URL
        )
        await new_chat.asave()  # Save asynchronously
        
        # Reply to the user with the response from the image handler
        await update.message.reply_text(response)
    else:
        # If not enough tokens, prompt the user to purchase more tokens
        keyboard = [[InlineKeyboardButton("خرید اعتبار", callback_data="buy_tokens")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "اعتبار شما به پایان رسیده.",
            reply_markup=reply_markup
        )

async def token_handler(user, message):
    """Check if the user has enough tokens across valid purchases.
       If yes, deduct tokens from the earliest valid plan(s) and return True; otherwise return False.
    """
    if message == "image processing":
        tokens_required = 10  # Fixed cost for image processing
    else:
        tokens_required = await num_tokens_from_string(message)
    
    available_tokens = await get_total_valid_tokens(user)
    if available_tokens >= tokens_required:
        success = await deduct_tokens_from_plans(user, tokens_required)
        if success:
            print(f"[record--status:successful] - {tokens_required} tokens deducted from user: {user.id}.")
            return True
        else:
            return False
    else:
        return False

def update_user_tokens(user, tokens_required):
    """reducing required token from the user tokens"""
    with transaction.atomic():
        # Deduct tokens and save the user data
        user.token -= tokens_required
        user.save()


async def num_tokens_from_string(string: str) -> int:
    """check how much the user input uses tokens"""
    encoding = tiktoken.encoding_for_model("gpt-4o")
    num_tokens = len(encoding.encode(string))
    return num_tokens
# New: Function to show token balance only.
async def show_active_token_plans(update: Update, context: CallbackContext):
    user = await user_data.objects.aget(id=update.effective_user.id)
    now = tzSale.now()
    # Retrieve all UserTokenPlan objects that have not yet expired.
    active_plans = await sync_to_async(list)(
        UserTokenPlan.objects.filter(user=user, expires_at__gte=now)
        .order_by('expires_at')
    )
    if active_plans:
        message = "طرح‌های توکنی فعال شما:\n\n"
        for plan in active_plans:
            # Format the expiry date as needed.
            exp_str = plan.expires_at.strftime("%Y-%m-%d")
            message += (
                f"• {plan.tokens_remaining} توکن (انقضا: {exp_str})\n"
            )
    else:
        message = "شما هیچ طرح توکنی فعال ندارید."
    
    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


# New: Function to show purchase options only.
async def purchase_tokens(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("کارت به کارت", callback_data="card_payment")]]
    # Query all token_price objects dynamically.
    options = await sync_to_async(list)(token_price.objects.all())
    for option in options:
        button_text = (
            f"{option.price} ریال - {option.token} توکن "
            f"(اعتبار: {option.validity_period} روز)"
        )
        callback_data = f"option_purchase_{option.option}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("منوی اصلی", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "برای افزایش اعتبار یکی از گزینه‌های زیر را انتخاب کنید:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def card_payment_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    card_text = await get_bot_text("card_option")
    await query.edit_message_text(
        text = card_text,
        reply_markup=reply_markup
    )

async def user_purchase_verifing(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    try:
        # Extract the token option id from the callback data.
        option_id = int(query.data.split("_")[-1])
    except Exception as e:
        await query.edit_message_text("خطا در شناسایی گزینه خرید.")
        return
    token_option = await token_price.objects.aget(option=option_id)
    keyboard = [
        [
            InlineKeyboardButton("لغو", callback_data="option_finalize_0"),
            InlineKeyboardButton("تایید", callback_data=f"option_finalize_{option_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"تعداد توکن دریافتی: {token_option.token}. آیا تایید می‌کنید؟",
        reply_markup=reply_markup
    )

async def purchase_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user = await user_data.objects.aget(id=update.effective_user.id)
    website = os.getenv("WEBSITE_URL")
    
    # Handle cancellation.
    if query.data == 'option_finalize_0':
        await query.edit_message_text(text='درخواست شما لغو شد.')
        return

    # Parse the token option id from the callback data.
    try:
        option_id = int(query.data.split("_")[-1])
    except Exception as e:
        await query.edit_message_text("خطا در شناسایی گزینه خرید.")
        return

    token_option = await token_price.objects.aget(option=option_id)
    new_invoice = invoices(
        user_id=user,
        token_plan=token_option,
        amount=token_option.price,
        status="HOLD",
        expires_at=tzSale.now() + timedelta(days=token_option.validity_period)
    )
    await new_invoice.asave()
    purchase_link = f"{website}/checkout/request/{new_invoice.id}"
    await query.edit_message_text(
        text=f"برای تکمیل خرید از طریق این لینک اقدام کنید: {purchase_link}"
    )

# async def optional_purchase_handler(update: Update, context: CallbackContext):
#     query = update.callback_query
#     await query.answer()
#     optional_purchase_text = await get_bot_text("optional_purchase", default="لطفا مبلغ دلخواه را به فرمت عدد انگیسی بدون هیچ علامت و یا کارکتری ارسال کنید توجه داشته باشید مبلغ ارسالی به ریال محاسبه میشود برای مثال: 2000000"
# )
#     await query.message.reply_text(
#         optional_purchase_text
#     )
#     context.user_data['awaiting_token_price'] = True

async def prompt_handler(update: Update, context: CallbackContext):
    # Create inline buttons for prompt options
    image_text = await get_bot_text("image_botton_text", default="پرامپت مخصوص عکس")
    general_text = await get_bot_text("general_botton_text", default="استفاده از هوش مصنوعی متنی")
    keyboard = [
        [
            InlineKeyboardButton(general_text, callback_data="set_mode_general"),
            InlineKeyboardButton(image_text, callback_data="set_mode_image_helper"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Show available tokens and display selection buttons
    # Handle both command and callback query
    prompt_handler_text = await get_bot_text("prompt_text", "برای استفاده از بات هدف خود را مشخص کنید:")
    if update.callback_query:
        await update.callback_query.edit_message_text(
            prompt_handler_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            prompt_handler_text,
            reply_markup=reply_markup
        )


async def set_prompt(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    user = await user_data.objects.aget(id=user_id)
    await query.answer()  # Acknowledge the callback

    # Determine which prompt was selected
    general_mode_text = await get_bot_text("general_mode_text", default="مدل شما به دستیار عمومی تغییر پیدا کرد. \nچجوری میتونم کمکتون کنم؟")
    image_mode_text = await get_bot_text("image_mode_text", default="مدل شما به دستیار پرامپت عکس تغییر یافت \n چه عکسی میخوای درست کنی و برای کدام هوش مصنوعی تا من بهت کمک کنم.")
    if query.data == "set_mode_general":
        await query.edit_message_text(
            text=general_mode_text
        )
        user.selected_prompt = 1
        await user.asave()
        print(
            f"[record--status:successful] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info: user: {user_id}, changed selected prompt to general."
        )
    elif query.data == "set_mode_image_helper":
        await query.edit_message_text(
            text=image_mode_text
        )
        user.selected_prompt = 2
        await user.asave()
        print(
            f"[record--status:successful] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info: user: {user_id}, changed selected prompt to image helper."
        )

async def model_handler(update: Update, context: CallbackContext):
    # Create inline buttons for model options
    keyboard = [
        [
            InlineKeyboardButton("gpt-4.0", callback_data="change_model_gpt_4"),
            InlineKeyboardButton("gpt-3.5", callback_data="change_model_gpt_3"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Handle both command and callback query
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "برای تغییر مدل هوش مصنوعی یکی را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "برای تغییر مدل هوش مصنوعی یکی را انتخاب کنید:",
            reply_markup=reply_markup
        )

async def set_model(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    user = await user_data.objects.aget(id=user_id)
    await query.answer()  # Acknowledge the callback

    # Check which model was selected
    if query.data == "change_model_gpt_4":
        await query.edit_message_text(
            text="""مدل دستیار هوشمند شما به gpt-4.0 تغییر کرد.
             می توانید با استفاده از چت جی پی تی 4.o سوالات خود را بپرسید. سلام چطوری می تونم کمکتون کنم؟
            """
        )
        user.selected_llm = "gpt-4o"
        await user.asave()
    elif query.data == "change_model_gpt_3":
        await query.edit_message_text(
            text="""مدل دستیار هوشمند شما به gpt-3.5 تغییر کرد.
             می توانید با استفاده از چت جی پی تی ۳.۵ سوالات خود را بپرسید. سلام چطوری می تونم کمکتون کنم؟
            """
        )
        user.selected_llm = "gpt-3.5-turbo"
        await user.asave()
 
 # Step 1: Define editinfo to display inline buttons       

async def change_user_info(update: Update, context: CallbackContext):
    # Create inline buttons for model options
    keyboard = [
        [
            InlineKeyboardButton("نام", callback_data="change_user_name"),
            InlineKeyboardButton("شماره", callback_data="change_user_number"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Display the model selection buttons
    await update.message.reply_text(
        "برای تغییر نام یا شماره تماس خود کلیک کنید:",
        reply_markup=reply_markup,
    )

# Add new handler functions
async def help_handler(update: Update, context: CallbackContext):
    help_text = await get_bot_text("help")
    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup)

async def policy_handler(update: Update, context: CallbackContext):
    policy_text = await get_bot_text("policy")
    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(policy_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(policy_text, reply_markup=reply_markup)

async def contact_us_handler(update: Update, context: CallbackContext):
    text = await get_bot_text("contact_us")
    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

    
# async def change_name(update: Update, context: CallbackContext):
#     query = update.callback_query
#     await query.answer()  # Acknowledge the callback
    
#     # Prompt the user to enter their new name
#     await query.edit_message_text("لطفا نام جدید خود را ارسال کنید:")
    
#     # Set the context for tracking the next user message as their new name
#     context.user_data['awaiting_name'] = True

# async def change_number(update: Update, context: CallbackContext):
#     query = update.callback_query
#     await query.answer()  # Acknowledge the callback
    
#     # Prompt the user to enter their new name
#     await query.edit_message_text("لطفا شماره جدید خود را ارسال کنید:")
    
#     # Set the context for tracking the next user message as their new name
#     context.user_data['awaiting_number'] = True

# Step 1: Show all active sale events
async def show_active_sales(update: Update, context: CallbackContext):
    now = tzSale.now()
    # Retrieve all active sales
    active_sales = await sync_to_async(list)(
        SaleEvent.objects.filter(start_time__lte=now, end_time__gte=now)
    )
    
    # Filter the sales further based on eligibility, if the event has an eligibility duration
    eligible_sales = []
    for sale in active_sales:
        if sale.eligible_duration:
            # Calculate the cutoff date: users must have registered after this date
            eligible_since = now - sale.eligible_duration
            # Assuming you have the user object already retrieved:
            user = await user_data.objects.aget(id=update.effective_user.id)
            if user.created_at >= eligible_since:
                eligible_sales.append(sale)
        else:
            # If no eligibility duration is set, all users can claim
            eligible_sales.append(sale)
    
    if not eligible_sales:
        no_sale = await get_bot_text(key="no_free_token")
        if update.callback_query:
            await update.callback_query.edit_message_text(no_sale)
        else:
            await update.message.reply_text(no_sale)
        return

    # Build the keyboard from eligible sales
    keyboard = []
    for sale in eligible_sales:
        button_text = f"{sale.name} - {sale.free_tokens}"
        callback_data = f"claim_sale_{sale.id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("منوی اصلی", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    sale_label = await get_bot_text(key="free_token_label")
    
    if update.callback_query:
        await update.callback_query.edit_message_text(sale_label, reply_markup=reply_markup)
    else:
        await update.message.reply_text(sale_label, reply_markup=reply_markup)

# Step 2: Handle the sale claim when a user clicks one of the buttons
async def claim_sale_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # acknowledge the callback

    user_id = update.effective_user.id
    user = await user_data.objects.aget(id=user_id)

    try:
        sale_id = int(query.data.split("_")[-1])
    except ValueError:
        await query.edit_message_text("خطا در شناسایی اعتبار رایگان.")
        return

    try:
        sale_event = await SaleEvent.objects.aget(id=sale_id)
    except SaleEvent.DoesNotExist:
        await query.edit_message_text("این اعتبار رایگان موجود نیست.")
        return

    now = tzSale.now()
    if sale_event.start_time > now or sale_event.end_time < now:
        await query.edit_message_text("این اعتبار رایگان در حال حاضر فعال نیست.")
        return

    # Check eligibility if eligible_duration is set.
    if sale_event.eligible_duration:
        eligible_since = now - sale_event.eligible_duration
        if user.created_at < eligible_since:
            await query.edit_message_text("شما برای استفاده از این اعتبار رایگان واجد شرایط نیستید.")
            return

    # Check if the user already claimed this sale event.
    claim_exists = await SaleClaim.objects.filter(user=user, sale_event=sale_event).aexists()
    if claim_exists:
        already_claimed = await get_bot_text(key="free_token_claim_error")
        await query.edit_message_text(already_claimed)
        return

    # Create a new UserTokenPlan record valid for one year from now.
    expiry_date = now + timedelta(days=365)
    new_plan = UserTokenPlan(
        user=user,
        token_plan=None,  # Since this is a free sale event, you can leave token_plan as None.
        tokens_remaining=sale_event.free_tokens,
        expires_at=expiry_date,
        invoice=None
    )
    await new_plan.asave()

    # Record the claim.
    new_claim = SaleClaim(user=user, sale_event=sale_event)
    await new_claim.asave()

    claim_success = await get_bot_text(key="free_token_claim_successful")
    await query.edit_message_text(claim_success)

async def generate_image_handler(update: Update, context: CallbackContext):
    # When the user sends the /generate_image command,
    # ask for a text prompt to generate an image.
    await update.message.reply_text("لطفاً متن توضیحی برای تولید تصویر وارد کنید:")
    context.user_data['awaiting_image_prompt'] = True


from checkout.models import UserTokenPlan

async def get_valid_token_plans(user):
    """Retrieve all active token plans (not expired and with remaining tokens) ordered by expiry."""
    now = tzSale.now()
    # Use sync_to_async to run ORM queries asynchronously.
    plans = await sync_to_async(list)(
        UserTokenPlan.objects.filter(user=user, expires_at__gte=now, tokens_remaining__gt=0).order_by('expires_at')
    )
    return plans

async def get_total_valid_tokens(user):
    """Sum up tokens remaining from all active token plans."""
    plans = await get_valid_token_plans(user)
    return sum(plan.tokens_remaining for plan in plans)

async def deduct_tokens_from_plans(user, tokens_required):
    """
    Deduct tokens_required from the user's valid token plans.
    The plans are already ordered by expires_at (soonest expiring first).
    If one plan has enough tokens, deduct from that plan; otherwise, combine tokens from multiple plans.
    """
    plans = await get_valid_token_plans(user)
    remaining = tokens_required
    
    # Try to find a single plan that can cover the required tokens.
    for plan in plans:
        if plan.tokens_remaining >= remaining:
            plan.tokens_remaining -= remaining
            await sync_to_async(plan.save)()
            return True

    # Otherwise, deduct from multiple plans in order of expiration.
    for plan in plans:
        if remaining <= 0:
            break
        if plan.tokens_remaining > 0:
            deduction = min(plan.tokens_remaining, remaining)
            plan.tokens_remaining -= deduction
            remaining -= deduction
            await sync_to_async(plan.save)()
    
    return remaining == 0


def main():
    print(
        f"[record--status:start] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info: bot started."
    )
    token = os.getenv("TOKEN")

    # Set up the application (bot) using the latest python-telegram-bot version
    application = Application.builder().token(token).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(sign_in_handler, pattern="^sign_in"))
    application.add_handler(CallbackQueryHandler(sign_in_handler, pattern="^verify"))
    application.add_handler(CallbackQueryHandler(sign_in_handler, pattern="^edit"))
    application.add_handler(CallbackQueryHandler(sign_in_handler, pattern="^edit_name"))
    application.add_handler(CallbackQueryHandler(sign_in_handler, pattern="^edit_number"))
    
    # Add main menu handler for both command and callback
    application.add_handler(CommandHandler("menu", main_menu_handler))
    application.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))

    application.add_handler(CommandHandler("token", show_active_token_plans))
    application.add_handler(CallbackQueryHandler(show_active_token_plans, pattern="^show_balance$"))
    application.add_handler(CallbackQueryHandler(purchase_tokens, pattern="^buy_tokens$"))
    application.add_handler(CallbackQueryHandler(card_payment_handler, pattern="^card_payment$"))
    application.add_handler(CallbackQueryHandler(user_purchase_verifing, pattern="^option_purchase_"))
    application.add_handler(CallbackQueryHandler(purchase_handler, pattern="^option_finalize_"))
    # application.add_handler(CallbackQueryHandler(optional_purchase_handler, pattern="^optional_purchase"))

    application.add_handler(CommandHandler("prompt", prompt_handler))
    application.add_handler(CallbackQueryHandler(prompt_handler, pattern="^change_prompt$"))

    application.add_handler(CallbackQueryHandler(set_prompt, pattern="^set_mode"))
    
    application.add_handler(CommandHandler("model", model_handler))
    application.add_handler(CallbackQueryHandler(model_handler, pattern="^show_model$"))
    application.add_handler(CallbackQueryHandler(set_model, pattern="^change_model"))
    
    application.add_handler(CommandHandler("editinfo", change_user_info))
    # application.add_handler(CallbackQueryHandler(change_name, pattern="change_user_name"))
    # application.add_handler(CallbackQueryHandler(change_number, pattern="change_user_number"))

    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("policy", policy_handler))
    application.add_handler(CallbackQueryHandler(help_handler, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(policy_handler, pattern="^policy$"))
    
    application.add_handler(CallbackQueryHandler(contact_us_handler, pattern="contact_us$"))
    # application.add.handler(CommandHandler('token' token_handler))

    application.add_handler(CommandHandler("freetoken", show_active_sales))
    # Handle any callback data starting with "claim_sale_"
    application.add_handler(CallbackQueryHandler(claim_sale_handler, pattern="^claim_sale_"))
    application.add_handler(CallbackQueryHandler(show_active_sales, pattern="^freetoken$"))

    application.add_handler(MessageHandler(filters.PHOTO, handle_photoes))  # Handle photo messages

    application.add_handler(CommandHandler("generate_image", generate_image_handler))


    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_texts)
    )  # Handle text messages
    # application.add_handler(MessageHandler(filters.PHOTO, handle_photoes))  # Handle photo messages

    # Start polling after scheduling jobs
    print(
        f"[record--status:start] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info: initial polling starts"
    )
    application.run_polling()


if __name__ == "__main__":
    main()
