# -*- coding: utf-8 -*-
import os, sys, json, threading, traceback
from pathlib import Path
from datetime import datetime

from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.image import AsyncImage
from kivy.uix.video import Video
from kivy.utils import platform

# KivyMD imports (متوافق مع 1.1.1)
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.dialog import MDDialog

from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout

# حاول استيراد MDTopAppBar أو MDToolbar أو fallback بسيط
try:
    from kivymd.uix.toolbar import MDTopAppBar
except Exception:
    try:
        from kivymd.uix.toolbar import MDToolbar as MDTopAppBar
    except Exception:
        class MDTopAppBar(MDBoxLayout):
            def __init__(self, title='', **kwargs):
                super().__init__(orientation='horizontal', size_hint_y=None, height=dp(56), **kwargs)
                self.add_widget(MDLabel(text=title, halign='left'))

# --- Arabic support: arabic-reshaper + bidi + font registration ---
AR_FONT_REGULAR = os.path.join('assets', 'fonts', 'NotoSansArabic-Regular.ttf')
AR_FONT_BOLD = os.path.join('assets', 'fonts', 'NotoSansArabic-Bold.ttf')

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    AR_SUPPORT = True
except Exception:
    AR_SUPPORT = False

if os.path.exists(AR_FONT_REGULAR):
    try:
        LabelBase.register(name='Roboto', fn_regular=AR_FONT_REGULAR,
                           fn_bold=AR_FONT_BOLD if os.path.exists(AR_FONT_BOLD) else AR_FONT_REGULAR)
    except Exception as e:
        print('Font register error:', e)
else:
    if sys.platform.startswith('win'):
        try:
            LabelBase.register(name='Roboto', fn_regular=r'C:\Windows\Fonts\arial.ttf')
        except Exception:
            pass

def _reshape_arabic(text: str) -> str:
    if not AR_SUPPORT or not isinstance(text, str):
        return text
    try:
        if any('\u0600' <= ch <= '\u06FF' or '\u0750' <= ch <= '\u08FF' for ch in text):
            reshaped = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped)
            return bidi_text
    except Exception:
        pass
    return text

def ar(t: str) -> str:
    return _reshape_arabic(t) if AR_SUPPORT else t

# --- Internationalization (simple) ---
if platform == 'android':
    try:
        from android.storage import primary_external_storage_path
        APP_DIR = Path(primary_external_storage_path()) / 'HeFedVideos'
    except Exception:
        APP_DIR = Path('/sdcard/HeFedVideos')
else:
    APP_DIR = Path.home() / 'HeFedVideos'

CONFIG_FILE = APP_DIR / 'config.json'
DEFAULT_CONFIG = {'lang': 'ar'}

def load_config():
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        print('Error saving config:', e)

config = load_config()
LANG = config.get('lang', 'ar')

TRANSLATIONS = {
    'app_title': {'en': 'HeFed Mobile', 'ar': 'HeFed Mobile'},
    'welcome': {'en': 'Welcome to HeFed Mobile!', 'ar': 'مرحباً في HeFed Mobile!'},
    'download_videos': {'en': 'Download videos', 'ar': 'تحميل الفيديوهات'},
    'enter_url': {'en': 'Enter video URL...', 'ar': 'أدخل رابط الفيديو...'},
    'paste': {'en': 'Paste', 'ar': 'لصق'},
    'download': {'en': 'Download', 'ar': 'تحميل'},
    'ready': {'en': 'Ready', 'ar': 'جاهز'},
    'downloading': {'en': 'Downloading...', 'ar': 'جاري التحميل...'},
    'download_complete': {'en': 'Download complete', 'ar': 'اكتمل التحميل'},
    'video': {'en': 'Video', 'ar': 'فيديو'},
    'play': {'en': 'Play', 'ar': 'تشغيل'},
    'pause': {'en': 'Pause', 'ar': 'إيقاف'},
    'delete': {'en': 'Delete', 'ar': 'حذف'},
    'library': {'en': 'My Library', 'ar': 'مكتبتي'},
    'no_videos': {'en': 'No videos\nPress Download to add videos', 'ar': 'لا توجد فيديوهات\nاضغط على تحميل لإضافة فيديوهات'},
    'confirm_delete_title': {'en': 'Confirm delete', 'ar': 'تأكيد الحذف'},
    'confirm_delete_text': {'en': "Delete '{title}'?", 'ar': "هل تريد حذف '{title}'؟"},
    'cancel': {'en': 'Cancel', 'ar': 'إلغاء'},
    'confirm': {'en': 'Delete', 'ar': 'حذف'},
    'settings': {'en': 'Settings', 'ar': 'الإعدادات'},
    'clear_all_videos': {'en': 'Clear all videos', 'ar': 'مسح كل الفيديوهات'},
    'open_video_folder': {'en': 'Open videos folder', 'ar': 'فتح مجلد الفيديوهات'},
    'files_info': {'en': 'Files: {count} • {size}', 'ar': 'عدد الملفات: {count} • {size}'},
    'confirm_clear_title': {'en': 'Confirm', 'ar': 'تأكيد'},
    'confirm_clear_text': {'en': 'All videos will be deleted. Continue?', 'ar': 'سيتم حذف كل الفيديوهات. متابعة؟'},
    'opening_path': {'en': 'Video path: {path}', 'ar': 'مسار الفيديو: {path}'},
    'file_missing': {'en': 'File not found', 'ar': 'الملف غير موجود'},
    'could_not_play': {'en': 'Could not play video', 'ar': 'تعذر تشغيل الفيديو'},
    'downloaded': {'en': 'Downloaded: {title}', 'ar': 'تم تحميل: {title}'},
    'language_changed_restart': {'en': 'Language changed.', 'ar': 'تم تغيير اللغة.'},
    'language_button_en': {'en': 'Switch to English', 'ar': 'تبديل إلى الإنجليزية'},
    'language_button_ar': {'en': 'Switch to Arabic', 'ar': 'تبديل إلى العربية'},
    'volume': {'en': 'Vol:', 'ar': 'صوت:'},
    'play_pause': {'en': 'Play/Pause', 'ar': 'تشغيل/إيقاف مؤقت'},
    'stop': {'en': 'Stop/Pause', 'ar': 'إيقاف/إيقاف مؤقت'},
}

def tr(key: str, **kwargs) -> str:
    s = TRANSLATIONS.get(key, {}).get(LANG)
    if s is None:
        s = TRANSLATIONS.get(key, {}).get('en', key)
    try:
        s = s.format(**kwargs) if kwargs else s
    except Exception:
        pass
    if LANG == 'ar':
        return ar(s)
    return s

VIDEO_DIR = APP_DIR / 'videos'
DB_FILE = APP_DIR / 'videos.json'
THUMBS_DIR = APP_DIR / 'thumbs'
APP_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

def load_db():
    if DB_FILE.exists():
        try:
            return json.loads(DB_FILE.read_text(encoding='utf-8'))
        except Exception:
            return []
    return []

def save_db(db):
    try:
        DB_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        print('Error saving DB:', e)

video_database = load_db()

def human_size(n):
    try:
        n = int(n)
    except Exception:
        return '0 KB'
    if n > 1024**3: return f"{n/(1024**3):.1f} GB"
    if n > 1024**2: return f"{n/(1024**2):.1f} MB"
    return f"{n/1024:.1f} KB"

def show_message(txt, duration=2):
    try:
        d = MDDialog(text=txt)
        d.open()
        Clock.schedule_once(lambda dt: d.dismiss(), duration)
    except Exception:
        try: print(txt)
        except: pass

def download_thumbnail(url, dest_path):
    try:
        import urllib.request
        urllib.request.urlretrieve(url, dest_path)
        return True
    except Exception:
        return False

try:
    import yt_dlp
except Exception:
    yt_dlp = None

try:
    from plyer import clipboard
except Exception:
    clipboard = None

# ---- حل مشكلة 'str object has no attribute write' عبر Logger مخصص ----
class _YTDLPLogger:
    def debug(self, msg):
        try: print('[yt-dlp]', msg)
        except: pass
    def info(self, msg):
        try: print('[yt-dlp]', msg)
        except: pass
    def warning(self, msg):
        try: print('[yt-dlp][WARN]', msg)
        except: pass
    def error(self, msg):
        try: print('[yt-dlp][ERROR]', msg)
        except: pass

class VideoDownloader:
    @staticmethod
    def download_video(url, progress_callback=None, complete_callback=None, error_callback=None):
        def progress_hook(d):
            try:
                status = d.get('status')
                if status == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes', 0)
                    percent = (downloaded/total*100) if total else 0.0
                    if progress_callback: progress_callback(percent, downloaded, total)
                elif status == 'finished':
                    if progress_callback: progress_callback(100, d.get('total_bytes',0), d.get('total_bytes',0))
            except Exception:
                pass

        def worker():
            if yt_dlp is None:
                if error_callback: error_callback('yt-dlp not installed. Run: pip install yt-dlp')
                return
            try:
                outtmpl = str(VIDEO_DIR / "%(title).200s.%(ext)s")
                opts = {
                    'outtmpl': outtmpl,
                    'format': 'best[height<=720]/best',
                    'progress_hooks': [progress_hook],
                    'quiet': True,
                    'noplaylist': True,
                    'no_warnings': True,
                    'ignoreerrors': True,
                    'extract_flat': False,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0'
                    },
                    'socket_timeout': 30,
                    'retries': 3,
                    'fragment_retries': 3,
                    'skip_unavailable_fragments': True,
                    # إضافة logger الآمن هنا لتجنب مشكلة "str object has no attribute write"
                    'logger': _YTDLPLogger(),
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        if error_callback: error_callback('Unable to extract video information'); return
                    info = ydl.extract_info(url, download=True)
                    try:
                        fname = ydl.prepare_filename(info)
                    except Exception:
                        fname = None
                    video_file = fname if fname and os.path.exists(fname) else None
                    if not video_file:
                        title = info.get('title','')
                        for f in VIDEO_DIR.iterdir():
                            if title and title[:30] in f.name:
                                video_file = str(f); break
                    if video_file:
                        thumb_url = info.get('thumbnail',''); thumb_local = ''
                        if thumb_url:
                            try:
                                ext = os.path.splitext(thumb_url)[1].split('?')[0] or '.jpg'
                                thumb_local = str(THUMBS_DIR / (Path(video_file).stem + ext))
                                if not os.path.exists(thumb_local):
                                    download_thumbnail(thumb_url, thumb_local)
                            except Exception:
                                thumb_local = ''
                        entry = {
                            'title': info.get('title','Video'),
                            'path': str(video_file),
                            'url': url,
                            'duration': info.get('duration',0),
                            'thumbnail': thumb_local or info.get('thumbnail',''),
                            'download_date': datetime.now().isoformat(),
                            'size': os.path.getsize(video_file) if os.path.exists(video_file) else 0,
                            'platform': info.get('extractor_key', 'Unknown'),
                        }
                        video_database.append(entry)
                        save_db(video_database)
                        if complete_callback: complete_callback(entry)
                    else:
                        if error_callback: error_callback('File not found after download')
            except Exception as e:
                error_msg = str(e)
                if 'Unsupported URL' in error_msg:
                    error_msg = 'Platform not supported or invalid URL'
                elif 'Private video' in error_msg:
                    error_msg = 'Video is private or unavailable'
                elif 'Video unavailable' in error_msg:
                    error_msg = 'Video is no longer available'
                if error_callback: error_callback(error_msg)

        threading.Thread(target=worker, daemon=True).start()

# ------------------ باقي واجهات المستخدم كما في الأصل ------------------

class VideoCard(MDCard):
    def __init__(self, video_info, on_play=None, on_delete=None, **kwargs):
        super().__init__(**kwargs)
        self.video_info = video_info
        self.on_play = on_play
        self.on_delete = on_delete
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = dp(8)
        self.elevation = 4

        layout = MDBoxLayout(orientation='horizontal', spacing=dp(10), padding=dp(8))
        thumb_src = video_info.get('thumbnail','')
        if thumb_src:
            thumb_widget = AsyncImage(source=thumb_src, size_hint=(None,1), width=dp(120))
        else:
            thumb_widget = MDCard(size_hint=(None,1), width=dp(120))
            thumb_widget.add_widget(MDLabel(text='🎬', halign='center', valign='middle', font_size='40sp'))

        info = MDBoxLayout(orientation='vertical')
        title_text = video_info.get('title', TRANSLATIONS['video'][LANG])
        title = MDLabel(text=ar(title_text) if LANG=='ar' else title_text, font_style='H6', size_hint_y=None, height=dp(36))

        meta_text = []
        d = video_info.get('duration') or 0
        try: d_int = int(d)
        except Exception: d_int = 0
        if d_int:
            mins, secs = divmod(d_int, 60); hours, mins = divmod(mins, 60)
            meta_text.append(f"{hours:02d}:{mins:02d}:{secs:02d}" if hours else f"{mins:02d}:{secs:02d}")
        if video_info.get('size'):
            meta_text.append(human_size(video_info['size']))
        if video_info.get('download_date'):
            meta_text.append(str(video_info['download_date']).split('T')[0])
        platform_name = video_info.get('platform','');
        if platform_name: meta_text.append(platform_name)

        meta_txt = ' • '.join(meta_text) if meta_text else tr('video')
        meta = MDLabel(text=ar(meta_txt) if LANG=='ar' else meta_txt, font_style='Caption', size_hint_y=None, height=dp(20))

        btns = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(8))
        btns.add_widget(MDRaisedButton(text=tr('play'), on_release=self._play))
        btns.add_widget(MDFlatButton(text=tr('delete'), on_release=self._delete))

        info.add_widget(title); info.add_widget(meta); info.add_widget(btns)
        layout.add_widget(thumb_widget); layout.add_widget(info)
        self.add_widget(layout)

    def _play(self, inst):
        if self.on_play: self.on_play(self.video_info)
    def _delete(self, inst):
        if self.on_delete: self.on_delete(self.video_info)

class DownloadScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.name='download'
        layout = MDBoxLayout(orientation='vertical', padding=dp(12), spacing=dp(12))
        self.header_label = MDLabel(text=tr('download_videos'), font_style='H5', halign='center')
        layout.add_widget(self.header_label)
        card = MDCard(elevation=6, radius=[12], padding=dp(12), size_hint_y=None, height=dp(180))
        vbox = MDBoxLayout(orientation='vertical', spacing=dp(8))
        self.url_input = MDTextField(hint_text=tr('enter_url'), multiline=False)
        hbox = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        self.paste_btn = MDFlatButton(text=tr('paste'), on_release=self._paste)
        self.download_btn = MDRaisedButton(text=tr('download'), on_release=self._start)
        hbox.add_widget(self.paste_btn); hbox.add_widget(self.download_btn)
        vbox.add_widget(self.url_input); vbox.add_widget(hbox)
        card.add_widget(vbox)
        self.progress_card = MDCard(radius=[10], padding=dp(10), size_hint_y=None, height=dp(120), opacity=0)
        pbox = MDBoxLayout(orientation='vertical', spacing=dp(6))
        self.progress_label = MDLabel(text=tr('ready'), size_hint_y=None, height=dp(30))
        self.progress_bar = MDProgressBar(value=0)
        self.progress_details = MDLabel(text='', font_style='Caption', size_hint_y=None, height=dp(20))
        pbox.add_widget(self.progress_label); pbox.add_widget(self.progress_bar); pbox.add_widget(self.progress_details)
        self.progress_card.add_widget(pbox)
        layout.add_widget(card); layout.add_widget(self.progress_card)
        self.add_widget(layout)

    def refresh_texts(self):
        self.header_label.text = tr('download_videos')
        self.url_input.hint_text = tr('enter_url')
        self.paste_btn.text = tr('paste')
        self.download_btn.text = tr('download')
        self.progress_label.text = tr('ready')

    def _paste(self, inst):
        try:
            if clipboard:
                txt = clipboard.paste()
                if txt: self.url_input.text = txt
            else: show_message(tr('could_not_play'))
        except Exception as e: show_message(str(e))

    @mainthread
    def _update_progress(self, percent, downloaded, total):
        self.progress_card.opacity = 1
        self.progress_bar.value = percent
        self.progress_label.text = tr('downloading') if percent < 100 else tr('download_complete')
        self.progress_details.text = f"{percent:.1f}% • {human_size(downloaded)}/{human_size(total)}"

    @mainthread
    def _done(self, entry):
        self.download_btn.disabled = False; self.url_input.text=''
        Clock.schedule_once(lambda dt: setattr(self.progress_card, 'opacity', 0), 2)
        show_message(tr('downloaded', title=entry.get('title', TRANSLATIONS['video'][LANG])), duration=2)

    @mainthread
    def _err(self, msg):
        self.download_btn.disabled = False; show_message(str(msg))
        Clock.schedule_once(lambda dt: setattr(self.progress_card, 'opacity', 0), 3)

    def _start(self, inst):
        url = self.url_input.text.strip()
        if not url:
            show_message(tr('enter_url')); return
        self.download_btn.disabled = True; self.progress_card.opacity = 1
        VideoDownloader.download_video(url, progress_callback=self._update_progress, complete_callback=self._done, error_callback=self._err)

class VideosScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.name='videos'
        root = MDBoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56))
        self.header_label = MDLabel(text=tr('library'), font_style='H5')
        header.add_widget(self.header_label)
        header.add_widget(MDIconButton(icon='refresh', on_release=lambda *a: self._refresh()))
        root.add_widget(header)
        scroll = ScrollView()
        self.list_box = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)
        self.add_widget(root)
        self._refresh()

    def refresh_texts(self):
        self.header_label.text = tr('library')
        self._refresh()

    def _refresh(self, *a):
        global video_database
        video_database = load_db()
        self.list_box.clear_widgets()
        if not video_database:
            c = MDCard(radius=[12], padding=dp(16), size_hint_y=None, height=dp(140))
            c.add_widget(MDLabel(text=tr('no_videos'), halign='center'))
            self.list_box.add_widget(c)
        else:
            for v in reversed(video_database):
                card = VideoCard(v, on_play=self._play, on_delete=self._delete)
                card.size_hint_y = None
                card.height = dp(120)
                self.list_box.add_widget(card)

    def _play(self, video_info):
        app = MDApp.get_running_app()
        app.player_screen.load_video(video_info)
        app.screen_manager.current = 'player'

    def _delete(self, video_info):
        def confirm(*a):
            global video_database
            video_database = [x for x in video_database if x.get('path') != video_info.get('path')]
            save_db(video_database)
            try:
                if os.path.exists(video_info.get('path')): os.remove(video_info.get('path'))
            except Exception as e: show_message(str(e))
            self._refresh(); dialog.dismiss()
        def cancel(*a): dialog.dismiss()
        dialog = MDDialog(title=tr('confirm_delete_title'),
                          text=tr('confirm_delete_text', title=video_info.get('title', TRANSLATIONS['video'][LANG])),
                          buttons=[MDFlatButton(text=tr('cancel'), on_release=cancel),
                                   MDRaisedButton(text=tr('confirm'), on_release=confirm)])
        dialog.open()

class PlayerScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.name='player'

        self.container = FloatLayout()
        self.add_widget(self.container)

        root = MDBoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6), size_hint=(1,1))
        top = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56))
        top.add_widget(MDIconButton(icon='arrow-left', on_release=lambda *a: self._back()))
        self.title_label = MDLabel(text=tr('video'), font_style='H6')
        top.add_widget(self.title_label)
        root.add_widget(top)

        self.video_widget = Video(state='stop', options={'allow_stretch': True}, size_hint_y=0.7)
        root.add_widget(self.video_widget)

        controls = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))
        self.play_btn = MDRaisedButton(text=tr('play'), on_release=self.toggle_play)
        self.stop_btn = MDFlatButton(text=tr('stop'), on_release=self.stop_video)
        controls.add_widget(self.play_btn); controls.add_widget(self.stop_btn)
        root.add_widget(controls)

        slider_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        self.time_label = MDLabel(text='00:00', size_hint_x=None, width=dp(70))
        self.progress_slider = Slider(min=0, max=1, value=0)
        self.progress_slider.bind(on_touch_down=self.on_seek_start, on_touch_up=self.on_seek_release)
        self.progress_slider.bind(value=self._on_slider_value_change)
        self.duration_label = MDLabel(text='00:00', size_hint_x=None, width=dp(70))
        slider_box.add_widget(self.time_label); slider_box.add_widget(self.progress_slider); slider_box.add_widget(self.duration_label)
        root.add_widget(slider_box)

        extra_controls = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))
        self.rewind_btn = MDIconButton(icon='rewind-10', on_release=self.rewind_video)
        extra_controls.add_widget(self.rewind_btn)
        self.forward_btn = MDIconButton(icon='fast-forward-10', on_release=self.forward_video)
        extra_controls.add_widget(self.forward_btn)
        self.volume_slider = Slider(min=0, max=1, value=1, size_hint_x=0.5)
        self.volume_slider.bind(value=self.on_volume_change)
        extra_controls.add_widget(MDLabel(text=tr('volume'), size_hint_x=None, width=dp(40)))
        extra_controls.add_widget(self.volume_slider)
        root.add_widget(extra_controls)

        self.container.add_widget(root)

        self.tooltip_card = MDCard(size_hint=(None,None), padding=dp(6), radius=[8], elevation=6)
        self.tooltip_label = MDLabel(text='', halign='center', size_hint=(None,None))
        self.tooltip_card.add_widget(self.tooltip_label)
        self.tooltip_card.size = (dp(88), dp(34))
        self.tooltip_card.opacity = 0
        self.container.add_widget(self.tooltip_card)

        self._event = None
        self._was_playing = False
        self._seeking = False

        self._preview_enabled = False
        self._preview_scheduled = None
        self._preview_pos_seconds = None

        # NEW: detected seek mode: 'seconds', 'fraction', or None
        self._seek_mode = None
        # track last known duration to re-run detection if duration changes
        self._last_duration = 0.0

    def refresh_texts(self):
        try:
            if LANG == 'ar':
                self.title_label.text = ar(self.title_label.text) if self.title_label.text else tr('video')
            else:
                self.title_label.text = self.title_label.text or tr('video')
        except Exception:
            pass
        try:
            self.play_btn.text = tr('pause') if getattr(self.video_widget, 'state','')=='play' else tr('play')
            self.stop_btn.text = tr('stop')
        except Exception:
            pass

    def load_video(self, info):
        path = info.get('path')
        if not path or not os.path.exists(path):
            show_message(tr('file_missing')); return

        title_text = info.get('title','')
        self.title_label.text = ar(title_text) if LANG == 'ar' else title_text

        try:
            self.video_widget.source = path
            self.video_widget.state = 'play'
            self.play_btn.text = tr('pause')
            if self._event: Clock.unschedule(self._event)
            self._event = Clock.schedule_interval(self._update_status, 0.5)
            # schedule seek-mode detection a bit after playback starts
            Clock.schedule_once(lambda dt: self._maybe_detect_seek_mode(), 0.6)
        except Exception:
            if not self._open_external(path): show_message(tr('could_not_play'))

    def _maybe_detect_seek_mode(self):
        # run detection only if duration known and changed
        try:
            dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
        except Exception:
            dur = 0.0
        if dur and abs(dur - self._last_duration) > 0.5:
            self._last_duration = dur
            self._detect_seek_mode()

    def _detect_seek_mode(self):
        """
        Detect whether video_widget.seek() expects seconds or fraction.
        We use a small safe test value (0.05) so both interpretations are small.
        After the small test, restore original position.
        """
        try:
            print("[DEBUG] Starting seek-mode detection...")
            orig = float(self.video_widget.position) if self.video_widget.position else 0.0
        except Exception:
            orig = 0.0
        dur = 0.0
        try:
            dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
        except Exception:
            dur = 0.0

        test_val = 0.05  # small value safe for both seconds and fraction
        verified = {'mode': None}

        def check_after_test(dt):
            try:
                pos = float(self.video_widget.position) if self.video_widget.position else 0.0
            except Exception:
                pos = 0.0
            # if pos approx test_val -> seconds mode
            if abs(pos - test_val) < 0.5:
                verified['mode'] = 'seconds'
            elif dur and abs(pos - (test_val * dur)) < max(1.0, 0.02*dur):
                verified['mode'] = 'fraction'
            else:
                verified['mode'] = None
            print(f"[DEBUG] detect_seek_mode: pos={pos:.3f}, dur={dur:.3f}, inferred_mode={verified['mode']}")
            # restore original position using safe method (use fraction if fraction detected, else seconds)
            if verified['mode'] == 'fraction' and dur:
                try:
                    self.video_widget.seek(orig / dur if dur else 0)
                except Exception:
                    try: setattr(self.video_widget, 'position', orig)
                    except Exception: pass
            else:
                try:
                    self.video_widget.seek(orig)
                except Exception:
                    try: setattr(self.video_widget, 'position', orig)
                    except Exception: pass
            # set mode
            self._seek_mode = verified['mode']
            print(f"[DEBUG] seek mode set to: {self._seek_mode}")

        # attempt test seek safely
        try:
            # call seek with small value; this will be interpreted either as seconds or fraction
            self.video_widget.seek(test_val)
        except Exception:
            try:
                setattr(self.video_widget, 'position', test_val)
            except Exception:
                pass
        # verify after short delay
        Clock.schedule_once(check_after_test, 0.18)

    def _update_status(self, dt):
        try:
            dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
            pos = float(self.video_widget.position) if self.video_widget.position else 0.0
            if dur > 0:
                if abs(self.progress_slider.max - dur) > 0.5:
                    print(f"[DEBUG] Setting slider.max = duration {dur}")
                    self.progress_slider.max = dur
                if not self._seeking:
                    self.progress_slider.value = pos
                self.time_label.text = self._format_time(pos)
                self.duration_label.text = self._format_time(dur)
            else:
                if not self._seeking:
                    self.progress_slider.value = min(1.0, pos) if pos else self.progress_slider.value
        except Exception:
            pass

    def _format_time(self, s):
        try:
            s = int(float(s))
            mins, secs = divmod(s, 60)
            hours, mins = divmod(mins, 60)
            if hours: return f"{hours:02d}:{mins:02d}:{secs:02d}"
            return f"{mins:02d}:{secs:02d}"
        except Exception:
            return '00:00'

    def toggle_play(self, inst):
        try:
            if self.video_widget.state == 'play':
                self.video_widget.state = 'pause'
                inst.text = tr('play')
            else:
                self.video_widget.state = 'play'
                inst.text = tr('pause')
        except Exception:
            pass

    def stop_video(self, inst):
        try:
            self.video_widget.state = 'pause'
            self.play_btn.text = tr('play')
        except Exception:
            pass

    def on_seek_start(self, slider, touch):
        if slider.collide_point(*touch.pos):
            try:
                self._seeking = True
                self._was_playing = (self.video_widget.state == 'play')
                if self._was_playing:
                    self.video_widget.state = 'pause'
                if self._preview_scheduled:
                    Clock.unschedule(self._preview_scheduled)
                self._preview_enabled = False
                self._preview_scheduled = Clock.schedule_once(lambda dt: self._enable_preview(), 0.4)
                dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
                frac = (touch.x - slider.x) / float(slider.width) if slider.width else 0
                frac = max(0.0, min(1.0, frac))
                pos = frac * dur if dur else frac
                try:
                    self.progress_slider.value = pos if slider.max > 1.001 else frac
                except Exception:
                    pass
            except Exception:
                pass
        return False

    def _enable_preview(self):
        self._preview_enabled = True
        self._show_preview_for_value(self.progress_slider.value)

    def _on_slider_value_change(self, instance, value):
        try:
            dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
            if self._preview_enabled and dur:
                if instance.max and instance.max > 1.001:
                    seconds = float(value)
                else:
                    seconds = float(value) * dur
                self._preview_pos_seconds = seconds
                self._show_preview_for_value(value)
        except Exception:
            pass

    def _show_preview_for_value(self, slider_value):
        try:
            dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
            if dur and self.progress_slider.max and self.progress_slider.max > 1.001:
                seconds = float(slider_value)
                frac = seconds / self.progress_slider.max if self.progress_slider.max else 0.0
            else:
                frac = float(slider_value)
                seconds = frac * dur if dur else 0.0
            seconds = max(0.0, min(seconds, dur if dur else seconds))
            self.tooltip_label.text = self._format_time(seconds)
            try:
                self.tooltip_label.texture_update()
                tex_w, tex_h = self.tooltip_label.texture_size
            except Exception:
                tex_w, tex_h = (dp(60), dp(12))
            w = max(dp(60), tex_w + dp(16)); h = max(dp(28), tex_h + dp(8))
            self.tooltip_card.size = (w, h)
            slider = self.progress_slider
            try:
                slider_window_x, _ = slider.to_window(slider.x, slider.y)
                container_window_x, _ = self.container.to_window(self.container.x, self.container.y)
                slider_x = slider_window_x - container_window_x
            except Exception:
                slider_x = slider.x
            frac_pos = (seconds / (self.progress_slider.max if self.progress_slider.max and self.progress_slider.max > 1.001 else (dur if dur else 1)))
            frac_pos = max(0.0, min(1.0, frac_pos))
            x = slider_x + frac_pos * max(0, slider.width)
            self.tooltip_card.pos = (x - self.tooltip_card.width/2, slider.y + slider.height + dp(8))
            self.tooltip_card.opacity = 1
        except Exception:
            pass

    def on_seek_release(self, slider, touch):
        if slider.collide_point(*touch.pos):
            try:
                if self._preview_scheduled:
                    Clock.unschedule(self._preview_scheduled)
                    self._preview_scheduled = None

                dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
                if self._preview_enabled and (self._preview_pos_seconds is not None):
                    target = self._preview_pos_seconds
                else:
                    if dur and slider.max and slider.max > 1.001:
                        target = float(slider.value)
                    else:
                        frac = float(slider.value)
                        target = frac * dur if dur else 0.0

                self._perform_verified_seek(target)

                self.tooltip_card.opacity = 0
                self._preview_enabled = False
                self._preview_pos_seconds = None

            except Exception:
                self._seeking = False
                try:
                    if self._was_playing:
                        self.video_widget.state = 'play'
                        self.play_btn.text = tr('pause')
                    else:
                        self.video_widget.state = 'pause'
                        self.play_btn.text = tr('play')
                except Exception:
                    pass
        return False

    def _perform_verified_seek(self, target_seconds):
        if target_seconds is None:
            return
        try:
            dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
        except Exception:
            dur = 0.0

        if dur and target_seconds is not None:
            target_seconds = max(0.0, min(target_seconds, dur))

        # Choose order according to detected seek-mode
        attempts = []
        if self._seek_mode == 'seconds':
            attempts = [('seek_seconds', lambda t: self._try_seek_seconds(t)),
                        ('set_position', lambda t: self._try_set_position(t)),
                        ('seek_fraction', lambda t: self._try_seek_fraction(t, dur))]
        elif self._seek_mode == 'fraction':
            attempts = [('seek_fraction', lambda t: self._try_seek_fraction(t, dur)),
                        ('set_position', lambda t: self._try_set_position(t)),
                        ('seek_seconds', lambda t: self._try_seek_seconds(t))]
        else:
            # unknown: try safe sequence (fraction first since calling seconds with big value may jump to end)
            attempts = [('seek_fraction', lambda t: self._try_seek_fraction(t, dur)),
                        ('seek_seconds', lambda t: self._try_seek_seconds(t)),
                        ('set_position', lambda t: self._try_set_position(t))]

        state = {'index': 0, 'target': target_seconds, 'dur': dur, 'attempts': attempts}
        self._seeking = True

        def try_next(dt=None):
            idx = state['index']
            if idx >= len(state['attempts']):
                print("[DEBUG] All seek methods tried and failed (or not verified). Restoring state.")
                self._seeking = False
                if self._was_playing:
                    self.video_widget.state = 'play'; self.play_btn.text = tr('pause')
                else:
                    self.video_widget.state = 'pause'; self.play_btn.text = tr('play')
                return
            name, fn = state['attempts'][idx]
            print(f"[DEBUG] Trying seek method #{idx}: {name} -> target {state['target']}")
            try:
                fn(state['target'])
            except Exception as e:
                print(f"[DEBUG] seek method {name} raised: {e}")
            Clock.schedule_once(verify, 0.18)
            state['index'] += 1

        def verify(dt):
            try:
                pos = float(self.video_widget.position) if self.video_widget.position else 0.0
            except Exception:
                pos = 0.0
            target = state['target']
            dur_local = state['dur']
            diff = abs(pos - target) if dur_local else abs(pos - target)
            tol = max(1.0, 0.02 * (dur_local if dur_local else 60))
            print(f"[DEBUG] verify: pos={pos:.2f}, target={target:.2f}, diff={diff:.2f}, tol={tol:.2f}")
            if diff <= tol:
                print(f"[DEBUG] Seek verified successful (pos ~ target). Using method index {state['index']-1}")
                self._seeking = False
                if self._was_playing:
                    self.video_widget.state = 'play'; self.play_btn.text = tr('pause')
                else:
                    self.video_widget.state = 'pause'; self.play_btn.text = tr('play')
                return
            else:
                print("[DEBUG] Verify failed, trying next method...")
                try_next()

        try_next()

    # low-level attempts
    def _try_seek_seconds(self, seconds):
        try:
            print(f"[DEBUG] _try_seek_seconds -> calling video.seek({seconds})")
            self.video_widget.seek(seconds)
        except Exception as e:
            print(f"[DEBUG] _try_seek_seconds exception: {e}")
            raise

    def _try_set_position(self, seconds):
        try:
            print(f"[DEBUG] _try_set_position -> setting position = {seconds}")
            setattr(self.video_widget, 'position', seconds)
        except Exception as e:
            print(f"[DEBUG] _try_set_position exception: {e}")
            raise

    def _try_seek_fraction(self, seconds, dur):
        try:
            frac = seconds / dur if dur else 0.0
            print(f"[DEBUG] _try_seek_fraction -> calling video.seek({frac}) (fraction)")
            self.video_widget.seek(frac)
        except Exception as e:
            print(f"[DEBUG] _try_seek_fraction exception: {e}")
            raise

    def rewind_video(self, inst):
        try:
            current_pos = float(self.video_widget.position) if self.video_widget.position else 0.0
            new_pos = max(0.0, current_pos - 10.0)
            self._perform_verified_seek(new_pos)
        except Exception:
            pass

    def forward_video(self, inst):
        try:
            current_pos = float(self.video_widget.position) if self.video_widget.position else 0.0
            dur = float(self.video_widget.duration) if self.video_widget.duration else 0.0
            new_pos = min(dur if dur else current_pos + 10.0, current_pos + 10.0)
            self._perform_verified_seek(new_pos)
        except Exception:
            pass

    def on_volume_change(self, instance, value):
        try:
            self.video_widget.volume = value
        except Exception:
            pass

    def _open_external(self, path):
        try:
            if platform == 'win': os.startfile(path); return True
            if platform == 'macosx' or sys.platform == 'darwin':
                import subprocess; subprocess.Popen(['open', path]); return True
            if platform == 'linux':
                import subprocess; subprocess.Popen(['xdg-open', path]); return True
            return False
        except Exception:
            return False

    def _back(self):
        try:
            if self._event: Clock.unschedule(self._event)
        except Exception:
            pass
        try: self.video_widget.state = 'stop'
        except Exception: pass
        MDApp.get_running_app().screen_manager.current = 'videos'

class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.name='settings'
        layout = MDBoxLayout(orientation='vertical', padding=dp(12), spacing=dp(12))
        layout.add_widget(MDLabel(text=tr('settings'), font_style='H5'))
        self.clear_btn = MDRaisedButton(text=tr('clear_all_videos'), on_release=self._clear_all)
        layout.add_widget(self.clear_btn)
        self.open_folder_btn = MDRaisedButton(text=tr('open_video_folder'), on_release=self._open_folder)
        layout.add_widget(self.open_folder_btn)
        lang_btn_text = tr('language_button_en') if LANG == 'ar' else tr('language_button_ar')
        self.lang_btn = MDRaisedButton(text=lang_btn_text, on_release=self._toggle_language)
        layout.add_widget(self.lang_btn)
        self.storage_label = MDLabel(text=tr('files_info', count=0, size='0 KB'), font_style='Caption')
        layout.add_widget(self.storage_label)
        self.add_widget(layout)
        self.storage_label.text = tr('files_info', count=self._storage_count(), size=human_size(self._storage_size()))

    def refresh_texts(self):
        try:
            self.clear_btn.text = tr('clear_all_videos')
            self.open_folder_btn.text = tr('open_video_folder')
            self.lang_btn.text = tr('language_button_en') if LANG == 'ar' else tr('language_button_ar')
            self.storage_label.text = tr('files_info', count=self._storage_count(), size=human_size(self._storage_size()))
        except Exception:
            pass

    def _storage_count(self):
        total=0; count=0
        for f in VIDEO_DIR.glob('*'):
            if f.is_file(): total += f.stat().st_size; count +=1
        return count

    def _storage_size(self):
        total=0
        for f in VIDEO_DIR.glob('*'):
            if f.is_file(): total += f.stat().st_size
        return total

    def _storage_text(self):
        total=self._storage_size(); count=self._storage_count()
        return tr('files_info', count=count, size=human_size(total))

    def _clear_all(self, inst):
        def confirm(*a):
            for f in VIDEO_DIR.glob('*'):
                try: f.unlink()
                except: pass
            global video_database
            video_database=[]; save_db(video_database)
            show_message(tr('download_complete')); dialog.dismiss()
        def cancel(*a): dialog.dismiss()
        dialog = MDDialog(title=tr('confirm_clear_title'), text=tr('confirm_clear_text'),
                          buttons=[MDFlatButton(text=tr('cancel'), on_release=cancel), MDRaisedButton(text=tr('confirm'), on_release=confirm)])
        dialog.open()

    def _open_folder(self, inst):
        try:
            if platform == 'win': os.startfile(str(VIDEO_DIR))
            elif platform == 'macosx' or sys.platform == 'darwin': import subprocess; subprocess.Popen(['open', str(VIDEO_DIR)])
            elif platform == 'linux': import subprocess; subprocess.Popen(['xdg-open', str(VIDEO_DIR)])
            else: show_message(tr('opening_path', path=str(VIDEO_DIR)))
        except Exception as e:
            show_message(str(e))

    def _toggle_language(self, inst):
        global LANG, config
        LANG = 'en' if LANG == 'ar' else 'ar'
        config['lang'] = LANG
        save_config(config)
        app = MDApp.get_running_app()
        if app:
            app.refresh_language()
        show_message(tr('language_changed_restart'), duration=2)

class HeFedMobileApp(MDApp):
    def build(self):
        if platform in ('linux','win','macosx'): Window.size=(380,760)
        root = MDBoxLayout(orientation='vertical')
        self.top_bar = MDTopAppBar(title=tr('app_title'), elevation=4)
        root.add_widget(self.top_bar)
        self.screen_manager = MDScreenManager()
        self.download_screen = DownloadScreen(); self.videos_screen = VideosScreen(); self.player_screen = PlayerScreen(); self.settings_screen = SettingsScreen()
        self.screen_manager.add_widget(self.download_screen); self.screen_manager.add_widget(self.videos_screen)
        self.screen_manager.add_widget(self.player_screen); self.screen_manager.add_widget(self.settings_screen)
        root.add_widget(self.screen_manager)
        bottom = MDBoxLayout(size_hint_y=None, height=dp(72), padding=dp(8))
        box = MDBoxLayout(orientation='horizontal', spacing=dp(8))
        box.add_widget(MDIconButton(icon='download', on_release=lambda *a: self.switch('download')))
        box.add_widget(MDIconButton(icon='play-circle', on_release=lambda *a: self.switch('videos')))
        box.add_widget(MDIconButton(icon='cog', on_release=lambda *a: self.switch('settings')))
        bottom.add_widget(box); root.add_widget(bottom)
        self.screen_manager.current = 'download'
        return root

    def refresh_language(self):
        try:
            self.top_bar.title = tr('app_title')
        except Exception:
            pass
        try: self.download_screen.refresh_texts()
        except Exception: pass
        try: self.videos_screen.refresh_texts()
        except Exception: pass
        try: self.player_screen.refresh_texts()
        except Exception: pass
        try: self.settings_screen.refresh_texts()
        except Exception: pass

    def switch(self, name):
        if name=='download':
            self.screen_manager.current='download'
        elif name=='videos':
            self.videos_screen._refresh()
            self.screen_manager.current='videos'
        elif name=='settings':
            self.settings_screen.storage_label.text = tr('files_info', count=self.settings_screen._storage_count(), size=human_size(self.settings_screen._storage_size()))
            self.screen_manager.current='settings'

    def on_start(self):
        Clock.schedule_once(lambda dt: show_message(tr('welcome'), duration=1.8), 0.6)

def main():
    try:
        HeFedMobileApp().run()
    except Exception as e:
        print('Error running app:', e); traceback.print_exc()

if __name__=='__main__':
    main()
