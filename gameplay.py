import json
import os
from typing import Dict, List
import random
from datetime import datetime
import math
import sys
import pygame

# Style tokens
GEODLE_BG = (250, 250, 250)
INK_900 = (22, 22, 22)
INK_700 = (64, 64, 64)
INK_500 = (120, 120, 120)
BORDER = (225, 225, 225)
PRIMARY = (9, 132, 105)      
ACCENT = (245, 245, 245)
BTN_BG = (0, 0, 0)
BTN_TEXT = (255, 255, 255)
GREEN = (30, 166, 114)
RED = (220, 68, 68)
BLUE = (64, 132, 246)
YELLOW = (246, 185, 59)

WHITE = (255, 255, 255)
GRAY_UI = (128, 128, 128)
TEAL = PRIMARY
GRAY = (128, 128, 128)
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
FPS = 60

# Confetti colors (used for win celebration)
CONFETTI_COLS = [
    (236, 99, 95), (255, 211, 102), (147, 221, 119),
    (123, 178, 255), (195, 155, 211)
]

def draw_round_rect(surf, rect, color, radius=8, width=0):
    x, y, w, h = rect if not isinstance(rect, pygame.Rect) else (rect.x, rect.y, rect.width, rect.height)
    r = min(radius, w//2, h//2)
    if r <= 0:
        pygame.draw.rect(surf, color, rect, width)
        return
    inner = pygame.Rect(x+r, y, w-2*r, h)
    pygame.draw.rect(surf, color, inner, width)
    inner = pygame.Rect(x, y+r, w, h-2*r)
    pygame.draw.rect(surf, color, inner, width)
    pygame.draw.circle(surf, color, (x+r, y+r), r, width)
    pygame.draw.circle(surf, color, (x+w-r-1, y+r), r, width)
    pygame.draw.circle(surf, color, (x+r, y+h-r-1), r, width)
    pygame.draw.circle(surf, color, (x+w-r-1, y+h-r-1), r, width)

def clamp(n, a, b):
    return max(a, min(n, b))

def ui_init(self, screen, game):
    self.screen = screen
    self.game = game
    self._init_fonts()
    self.max_width = 960
    self.padding_y = 18
    self.line_h = 28
    self.input_h = 44
    self.cell_h = 40
    self.row_h = 44
    self.table_header_h = 36
    self.table_border = 1
    self.hover_row = -1
    self.show_help = True
    self._input_rect = pygame.Rect(0,0,0,0)
    self._submit_rect = pygame.Rect(0,0,0,0)
    self._sugg_rects = []
    self.input_focused = False
    self.sugg_scroll_idx = 0
    self._suggest_drop_rect = None
    self._suggest_track_rect = None
    self._suggest_thumb_rect = None
    self._dragging_sugg_thumb = False
    self._drag_thumb_offset = 0

    self.logo_rect = pygame.Rect(16, 12, 140, 56)
    self.logo_surf = None
    try:
        base = os.path.dirname(__file__)
        # Prefer packaged logo in img/, fallback to package root logo.png
        logo_candidates = [
            os.path.join(base, 'img', 'logo.png'),
            os.path.join(base, 'logo.png'),
        ]
        for path in logo_candidates:
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.logo_surf = img
                    break
                except Exception:
                    self.logo_surf = None
    except Exception:
        self.logo_surf = None


class CountryData:
    def __init__(self, name: str, continent: str, population: int, 
                 landlocked: bool, religion: str, temperature: float, government: str):
        self.name = name
        self.continent = continent
        self.population = population
        self.landlocked = landlocked
        self.religion = religion
        self.temperature = temperature  # Celsius
        self.government = government
    
    def get_data_list(self):
        return [self.continent, self.population, self.landlocked, 
                self.religion, self.temperature, self.government]
    
    @staticmethod
    def get_headers():
        return ['Continent', 'Population', 'Landlocked', 'Religion', 'Avg. Temp.', 'Gov.']


class CountryDatabase:
    def __init__(self):
        self.countries = {}
        base = os.path.dirname(__file__)
        self.epoch = datetime(2022, 5, 9)
        loaded = False
        path = os.path.join(base, 'src', 'country.json')
        loaded = False
        if os.path.exists(path):
            loaded = self.load_from_country_json(os.path.dirname(path))
        if not loaded:
            raise RuntimeError(f"Failed to load country.json!")
    def load_json_file(self, data_dir: str, filename: str):
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def load_from_country_json(self, data_dir: str) -> bool:
        merged = data_dir
        if os.path.isdir(data_dir):
            merged = os.path.join(data_dir, 'country.json')
        if os.path.exists(merged):
            try:
                arr = self.load_json_file(os.path.dirname(merged), os.path.basename(merged))
                loaded = 0
                for item in arr:
                    if not isinstance(item, dict):
                        continue
                    name = (item.get('country') or item.get('name') or '').strip()
                    if not name:
                        continue
                    try:
                        population = int(item.get('population') or item.get('pop') or 0)
                    except Exception:
                        population = 0
                    try:
                        temp = float(item.get('temperature') or item.get('avg_temp') or 0.0)
                    except Exception:
                        temp = 0.0
                    land = item.get('landlocked', item.get('is_landlocked', False))
                    land = str(land).strip() in ('1', 'true', 'True', 'yes')
                    country = CountryData(
                        name=name,
                        continent=item.get('continent') or item.get('region') or '',
                        population=population,
                        landlocked=land,
                        religion=item.get('religion') or item.get('dominant_religion') or '',
                        temperature=temp,
                        government=item.get('government') or item.get('gov') or ''
                    )
                    self.countries[country.name] = country
                    loaded += 1
                return loaded > 0
            except Exception:
                return False
        return len(self.countries) > 0
    
    def get_country_of_day(self) -> CountryData:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        day_number = (today - self.epoch).days
        country_names = list(self.countries.keys())
        selected_name = country_names[day_number % len(country_names)]
        return self.countries[selected_name]

    def search_countries(self, query: str) -> List[str]:
        if not query:
            return []
        query_lower = query.lower()
        matches = [name for name in self.countries.keys() 
                  if query_lower in name.lower()]
        return sorted(matches)[:10]


class GeodleGame:
    def __init__(self):
        self.database = CountryDatabase()
        self.correct_country = self.database.get_country_of_day()
        self.guesses: List[CountryData] = []
        self.max_guesses = 6
        self.game_over = False
        self.won = False
        self.current_input = ""
        self.suggestions: List[str] = []
        self.selected_suggestion = 0
        self.error_message = ""
        self.error_timer = 0
        self.particles = []

    def make_guess(self, country_name: str) -> bool:
        if country_name not in self.database.countries:
            self.error_message = "Country not found!"
            self.error_timer = 120
            return False
        if any(g.name == country_name for g in self.guesses):
            self.error_message = "Already guessed this country!"
            self.error_timer = 120
            return False
        country_data = self.database.countries[country_name]
        self.guesses.append(country_data)
        if country_name == self.correct_country.name:
            self.won = True
            self.game_over = True
            try:
                self.spawn_confetti()
            except Exception:
                pass
        elif len(self.guesses) >= self.max_guesses:
            self.game_over = True
        return True

    def is_approx_equal(self, a: float, b: float, max_diff_percent: float = 0.1) -> bool:
        avg = (a + b) / 2
        if avg == 0:
            return a == b
        percent_diff = abs(a - b) / avg
        return percent_diff <= max_diff_percent

    def get_hint_indicator(self, correct_val, guess_val) -> str:
        if isinstance(correct_val, bool) or isinstance(correct_val, str):
            return 'correct' if correct_val == guess_val else 'wrong'
        if self.is_approx_equal(correct_val, guess_val):
            return 'correct'
        elif guess_val < correct_val:
            return 'higher'
        else:
            return 'lower'

    def update(self):
        if self.error_timer > 0:
            self.error_timer -= 1
            if self.error_timer == 0:
                self.error_message = ""
        try:
            self.update_confetti(1.0 / FPS)
        except Exception:
            pass

    def spawn_confetti(self):
        cx = WINDOW_WIDTH // 2
        for _ in range(140):
            angle = random.uniform(-math.pi, 0)
            speed = random.uniform(120, 300)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.randint(3, 6)
            color = random.choice(CONFETTI_COLS)
            life = random.uniform(1.2, 2.0)
            self.particles.append([cx + random.uniform(-60, 60), 60, vx, vy, size, color, life])

    def update_confetti(self, dt: float):
        gravity = 400
        new = []
        for p in self.particles:
            x, y, vx, vy, s, color, life = p
            vy += gravity * dt
            x += vx * dt
            y += vy * dt
            life -= dt
            if life > 0 and y < WINDOW_HEIGHT + 20:
                new.append([x, y, vx, vy, s, color, life])
        self.particles = new


class UI:
    def __init__(self, screen, game):
        ui_init(self, screen, game)

    def render(self):
        self.screen.fill(GEODLE_BG)
        sw, sh = self.screen.get_size()
        cx = sw // 2
        left = cx - self.max_width // 2
        y = 32
        try:
            if getattr(self, 'logo_surf', None):
                self.screen.blit(self.logo_surf, (self.logo_rect.left + 4, self.logo_rect.top + 4))
            else:
                draw_round_rect(self.screen, self.logo_rect, ACCENT, radius=8, width=0)
                pygame.draw.rect(self.screen, BORDER, self.logo_rect, width=1, border_radius=8)
                ltxt = self.f_small.render("LOGO", True, INK_500)
                self.screen.blit(ltxt, (self.logo_rect.left + 10, self.logo_rect.centery - ltxt.get_height()//2))
            y = max(y, self.logo_rect.bottom + 8)
        except Exception:
            y = 32

        # Title
        y = self._draw_title(left, y)

        try:
            remaining = getattr(self.game, 'max_guesses', 6) - len(getattr(self.game, 'guesses', []) or [])
        except Exception:
            remaining = 6
        rem_s = self.f_small.render(f"{remaining} guesses remaining", True, INK_700)
        rem_rect = rem_s.get_rect()
        rem_rect.centerx = self.screen.get_width() // 2
        rem_rect.top = y
        self.screen.blit(rem_s, rem_rect)
        y = rem_rect.bottom + 8

        # Search bar
        y += 10
        y = self._draw_search(left, y)

        # Help / How to play
        y += 12
        if self.show_help:
            y = self._draw_help(left, y)

        y += 8
        self._draw_table(left, y, sw)
        self._draw_suggestions_overlay()
        self._draw_blinking_caret()

        # Draw confetti particles if any
        try:
            for x, y, vx, vy, s, color, life in getattr(self.game, 'particles', []):
                pygame.draw.rect(self.screen, color, pygame.Rect(int(x), int(y), s, s))
        except Exception:
            pass

        self._draw_game_over()

    def handle_mouse(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._update_hover_row(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if getattr(self, '_restart_rect', None) and self._restart_rect.collidepoint(event.pos):
                try:
                    new_game = enhance()
                    
                    try:
                        existing = self.game
                        for k in list(existing.__dict__.keys()):
                            if k not in new_game.__dict__:
                                del existing.__dict__[k]
                        for k, v in new_game.__dict__.items():
                            existing.__dict__[k] = v
                    except Exception:
                        self.game = new_game
                    try:
                        print(f"\nToday's country: {new_game.correct_country.name}")
                    except Exception:
                        pass
                    self._sugg_rects = []
                    self.input_focused = False
                except Exception:
                    pass
                return
            if getattr(self, '_quit_rect', None) and self._quit_rect.collidepoint(event.pos):
                try:
                    pygame.quit()
                    import sys
                    sys.exit(0)
                except SystemExit:
                    raise

            # Submit
            if self._submit_rect.collidepoint(event.pos):
                self._try_submit()
                self.input_focused = False

            for idx, r in enumerate(self._sugg_rects):
                if r.collidepoint(event.pos):
                    self.game.selected_suggestion = self.sugg_scroll_idx + idx
                    self._try_submit()
                    return

            if getattr(self, '_suggest_track_rect', None) and self._suggest_track_rect.collidepoint(event.pos):
                track = self._suggest_track_rect
                rel = (event.pos[1] - track.top) / max(1, track.height)
                total = len(getattr(self.game, 'suggestions', []))
                max_show = min(6, total)
                new_start = int(rel * max(0, total - max_show))
                self.sugg_scroll_idx = clamp(new_start, 0, max(0, total - max_show))
                return

            if getattr(self, '_suggest_thumb_rect', None) and self._suggest_thumb_rect.collidepoint(event.pos):
                self._dragging_sugg_thumb = True
                self._drag_thumb_offset = event.pos[1] - self._suggest_thumb_rect.top
                return

            if self._input_rect.collidepoint(event.pos):
                self.input_focused = True
            else:
                self.input_focused = False
                self.game.suggestions = []

        elif event.type == pygame.MOUSEWHEEL:
            if getattr(self, '_suggest_drop_rect', None) and self._suggest_drop_rect.collidepoint(pygame.mouse.get_pos()):
                total = len(getattr(self.game, 'suggestions', []) or [])
                if total:
                    max_show = min(6, total)
                    self.sugg_scroll_idx = clamp(
                        self.sugg_scroll_idx - event.y,  # small per-notch step
                        0, max(0, total - max_show)
                    )

        elif event.type == pygame.MOUSEMOTION and getattr(self, '_dragging_sugg_thumb', False):
            if getattr(self, '_suggest_track_rect', None) is None or getattr(self, '_suggest_thumb_rect', None) is None:
                return
            track = self._suggest_track_rect
            thumb_h = self._suggest_thumb_rect.height
            new_top = clamp(event.pos[1] - self._drag_thumb_offset, track.top, track.bottom - thumb_h)
            prop = (new_top - track.top) / max(1, (track.height - thumb_h))
            total = len(getattr(self.game, 'suggestions', []) or [])
            max_show = min(6, total)
            max_start = max(0, total - max_show)
            self.sugg_scroll_idx = int(round(prop * max_start))
            return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and getattr(self, '_dragging_sugg_thumb', False):
            self._dragging_sugg_thumb = False
            return

    def _update_hover_row(self, pos):
        table_top = getattr(self, "_table_top", None)
        table_cols = getattr(self, "_table_cols", [])
        rows = getattr(self, "_table_rows", 0)
        if not table_top: 
            self.hover_row = -1
            return
        x, y = pos
        left, top = table_top
        if x < left or x > left + sum(table_cols):
            self.hover_row = -1
            return
        header_h = self.table_header_h + self.table_border
        y_rel = y - (top + header_h)
        if y_rel < 0:
            self.hover_row = -1
            return
        row = int(y_rel // self.row_h)
        self.hover_row = row if 0 <= row < rows else -1

    def _init_fonts(self):
        pygame.font.init()
        self.f_title = pygame.font.SysFont("Inter, Helvetica, Arial", 56, bold=True)
        self.f_sub = pygame.font.SysFont("Inter, Helvetica, Arial", 18)
        self.f_label = pygame.font.SysFont("Inter, Helvetica, Arial", 16)
        self.f_small = pygame.font.SysFont("Inter, Helvetica, Arial", 14)
        self.f_button = pygame.font.SysFont("Inter, Helvetica, Arial", 16, bold=True)

    def _draw_title(self, left, y):
        title = self.f_title.render("Geodle", True, PRIMARY)
        sub = self.f_sub.render("A Wordle-ish geography game", True, INK_700)
        trect = title.get_rect()
        srect = sub.get_rect()
        sw = self.screen.get_width()
        trect.centerx = sw // 2
        srect.centerx = sw // 2
        trect.top = y
        srect.top = y + trect.height + 2
        self.screen.blit(title, trect)
        self.screen.blit(sub, srect)
        return srect.bottom + 16

    def _draw_search(self, left, y):
        input_w = int(self.max_width * 0.7)
        submit_w = 110
        gap = 8
        total_w = input_w + gap + submit_w
        sw = self.screen.get_width()
        group_left = sw // 2 - total_w // 2
        self._input_rect = pygame.Rect(group_left, y, input_w, self.input_h)
        self._submit_rect = pygame.Rect(self._input_rect.right + gap, y, submit_w, self.input_h)

        # Input box
        draw_round_rect(self.screen, self._input_rect, (0,0,0), radius=10, width=1)
        draw_round_rect(self.screen, self._input_rect.inflate(-2,-2), ACCENT, radius=10, width=0)
        txt = self.game.current_input if getattr(self.game, "current_input", "") else ""
        if txt:
            surf = self.f_label.render(txt, True, INK_900)
        else:
            surf = self.f_label.render("Country", True, INK_500)
        self.screen.blit(surf, (self._input_rect.left + 12, self._input_rect.centery - surf.get_height()//2))

        # Submit
        draw_round_rect(self.screen, self._submit_rect, BTN_BG, radius=10, width=0)
        sub = self.f_button.render("SUBMIT", True, BTN_TEXT)
        self.screen.blit(sub, (self._submit_rect.centerx - sub.get_width()//2,
                               self._submit_rect.centery - sub.get_height()//2))

        # dropdown
        self._sugg_rects = []
        suggs = getattr(self.game, "suggestions", []) or []
        if suggs:
            max_show = min(6, len(suggs))
            drop_h = max_show * self.cell_h
            drop = pygame.Rect(self._input_rect.left, self._input_rect.bottom + 6,
                               self._input_rect.width, drop_h)
            pygame.draw.rect(self.screen, BORDER, drop, border_radius=10)
            pygame.draw.rect(self.screen, (255,255,255), drop.inflate(-2,-2), border_radius=10)
            for i in range(max_show):
                r = pygame.Rect(drop.left+4, drop.top + i*self.cell_h + 4, drop.width-8, self.cell_h-6)
                if i == getattr(self.game, "selected_suggestion", 0):
                    pygame.draw.rect(self.screen, (240, 248, 255), r, border_radius=8)
                label = self.f_small.render(suggs[i], True, INK_900)
                self.screen.blit(label, (r.left + 10, r.centery - label.get_height()//2))
                self._sugg_rects.append(r)

        return max(self._submit_rect.bottom, self._input_rect.bottom) + 12

    def _draw_help(self, left, y):
        # “How to Play”
        dot = self.f_label.render("!", True, INK_700)
        h = self.f_label.render("How to Play", True, INK_900)
        sw = self.screen.get_width()
        dx = sw//2 - (dot.get_width() + 8 + h.get_width())//2
        self.screen.blit(dot, (dx, y))
        self.screen.blit(h, (dx + dot.get_width() + 8, y))
        y += self.line_h

        help_lines = [
            "Figure out the secret country in 6 guesses!",
            "Each guess must be a country that appears in the search box.",
            "After each guess, you get hints for Continent, Population, Landlocked, Religion, Avg. Temp., and Government.",
        ]
        for line in help_lines:
            s = self.f_small.render(line, True, INK_700)
            srect = s.get_rect()
            srect.centerx = self.screen.get_width() // 2
            srect.top = y
            self.screen.blit(s, srect)
            y += self.line_h - 4
        return y

    def _draw_header_cell(self, x, y, w, title):
        rect = pygame.Rect(x, y, w, self.table_header_h)
        pygame.draw.rect(self.screen, BORDER, rect, width=self.table_border)
        label = self.f_small.render(title, True, INK_700)
        self.screen.blit(label, (rect.centerx - label.get_width()//2, rect.centery - label.get_height()//2))
        return rect

    def _draw_hint_square(self, rect: pygame.Rect, status: str, extra: str = ""):
        if status not in ("good", "bad", "up", "down"):
            status = "bad"

        color = GREEN if status == "good" else (BLUE if status in ("up", "down") else RED)

        size = min(rect.width, rect.height) - 14
        x = rect.centerx - size // 2
        y = rect.centery - size // 2
        pygame.draw.rect(self.screen, color, (x, y, size, size), border_radius=6)

        if status in ("up", "down"):
            tri_h = size // 2
            cx, cy = rect.centerx, rect.centery
            pts = ([(cx, cy - tri_h // 2), (cx - tri_h // 2, cy + tri_h // 2), (cx + tri_h // 2, cy + tri_h // 2)]
                if status == "up"
                else [(cx, cy + tri_h // 2), (cx - tri_h // 2, cy - tri_h // 2), (cx + tri_h // 2, cy - tri_h // 2)])
            pygame.draw.polygon(self.screen, (255, 255, 255), pts)

    def _status_from_result(self, result, key) -> str:
    # pull value
        val = result.get(key, None) if isinstance(result, dict) else getattr(result, key, None)

        if key in ("continent", "landlocked", "religion", "government"):
            return "good" if val in ("match", True, "same") else "bad"

        if key == "population":
            try:
                return "good" if abs(float(val)) <= 0.10 else "bad"
            except Exception:
                return "bad"

        if key == "temperature":
            if val in ("up", "down"):
                return val
            return "good" if val in ("match", True) else "bad"

        return "bad"


    def _g_cols(self) -> List[int]:
        return [210, 120, 110, 120, 120, 140, 140]

    def _draw_table(self, left, y, sw):
        cols = self._g_cols()
        if len(cols) < 7:
            cols = [210, 120, 110, 120, 120, 140, 140]
        self._table_cols = cols
        x = left
        top = y
        # headers
        headers = ["Country", "Continent", "Population", "Landlocked", "Religion", "Avg. Temp.", "Gov."]
        hx = x
        for i, w in enumerate(cols):
            # avoid header overflow
            title = headers[i] if i < len(headers) else ""
            self._draw_header_cell(hx, y, w, title)
            hx += w
        y += self.table_header_h + self.table_border

        raw_guesses = getattr(self.game, "guesses", []) or []
        guesses = []
        for g in raw_guesses:
            result = {}
            correct = getattr(self.game, 'correct_country', None)
            if correct:
                result['continent'] = 'match' if getattr(g, 'continent', None) == getattr(correct, 'continent', None) else None
                try:
                    gv = float(getattr(g, 'population', 0))
                    cv = float(getattr(correct, 'population', 1))
                    result['population'] = (gv - cv) / max(abs(cv), 1)
                except Exception:
                    result['population'] = None
                result['landlocked'] = 'match' if getattr(g, 'landlocked', None) == getattr(correct, 'landlocked', None) else None
                result['religion'] = 'match' if getattr(g, 'religion', None) == getattr(correct, 'religion', None) else None
                try:
                    gv = float(getattr(g, 'temperature', 0.0))
                    cv = float(getattr(correct, 'temperature', 0.0))
                    if abs(gv - cv) <= 0.5:
                        result['temperature'] = 'match'
                    elif gv < cv:
                        result['temperature'] = 'up'
                    else:
                        result['temperature'] = 'down'
                except Exception:
                    result['temperature'] = None
                result['government'] = 'match' if getattr(g, 'government', None) == getattr(correct, 'government', None) else None

            guesses.append((g, result))
        self._table_rows = len(guesses)
        self._table_top = (left, top)

        for r_idx, guess in enumerate(guesses):
            g_country, g_result = (None, None)
            if isinstance(guess, tuple) and len(guess) >= 2:
                g_country, g_result = guess[0], guess[1]
            else:
                g_country = guess

            country_name = getattr(g_country, "name", str(g_country))

            row_rect = pygame.Rect(left, y, sum(cols), self.row_h)
            if r_idx == self.hover_row:
                pygame.draw.rect(self.screen, (245, 248, 252), row_rect)

            cx = left
            pygame.draw.rect(self.screen, BORDER, (cx, y, cols[0], self.row_h), width=self.table_border)
            name_s = self.f_small.render(country_name, True, INK_900)
            self.screen.blit(name_s, (cx + 12, y + (self.row_h - name_s.get_height())//2))
            cx += cols[0]

            # Hint cells
            keys = ["continent", "population", "landlocked", "religion", "temperature", "government"]
            for i in range(len(keys)):
                col_index = i + 1
                w = cols[col_index] if col_index < len(cols) else 120
                pygame.draw.rect(self.screen, BORDER, (cx, y, w, self.row_h), width=self.table_border)
                if g_result is not None:
                    status = self._status_from_result(g_result, keys[i])
                else:
                    status = "unknown"
                self._draw_hint_square(pygame.Rect(cx, y, w, self.row_h), status)
                cx += w

            y += self.row_h
        if not guesses:
            hint = self.f_small.render("Your hints will appear here after each guess.", True, INK_500)
            self.screen.blit(hint, (left + 12, y + 8))

    def _draw_blinking_caret(self):
        if not getattr(self, "input_focused", False):
            return

        visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if not visible:
            return

        txt = self.game.current_input if getattr(self.game, "current_input", "") else ""
        if txt:
            surf = self.f_label.render(txt, True, INK_900)
            caret_x = self._input_rect.left + 12 + surf.get_width()
        else:
            caret_x = self._input_rect.left + 12

        caret_y = self._input_rect.centery
        caret_surf = self.f_label.render("|", True, INK_900)
        self.screen.blit(caret_surf, (caret_x, caret_y - caret_surf.get_height()//2))
    def _draw_suggestions_overlay(self):
        suggs = getattr(self.game, 'suggestions', None)
        if not suggs:
            self._sugg_rects = []
            self._suggest_drop_rect = None
            self._suggest_track_rect = None
            return

        total = len(suggs)
        max_show = min(6, total)
        drop_h = max_show * self.cell_h

        drop = pygame.Rect(self._input_rect.left,
                        self._input_rect.bottom + 6,
                        self._input_rect.width,
                        drop_h)

        draw_round_rect(self.screen, drop, BORDER, radius=10, width=1)
        draw_round_rect(self.screen, drop.inflate(-2, -2), WHITE, radius=10, width=0)

        self._sugg_rects = []
        inner = drop.inflate(-8, -8)

        self.sugg_scroll_idx = clamp(self.sugg_scroll_idx, 0, max(0, total - max_show))
        sel = getattr(self.game, 'selected_suggestion', 0)
        if sel < self.sugg_scroll_idx:
            self.sugg_scroll_idx = sel
        elif sel >= self.sugg_scroll_idx + max_show:
            self.sugg_scroll_idx = sel - max_show + 1

        start = self.sugg_scroll_idx

        for i in range(max_show):
            idx = start + i
            r = pygame.Rect(inner.left, inner.top + i*self.cell_h, inner.width, self.cell_h)

            bg = (240, 248, 255) if idx == sel else WHITE
            pygame.draw.rect(self.screen, bg, r, border_radius=6)
            if i < max_show - 1:
                pygame.draw.line(self.screen, BORDER, (r.left, r.bottom-1), (r.right, r.bottom-1), 1)

            name = suggs[idx]
            meta = ""
            try:
                cd = self.game.database.countries.get(name)
                if cd:
                    meta = f"{cd.continent}, {cd.population:,}, {cd.government}"
            except Exception:
                pass

            name_s = self.f_label.render(name, True, INK_900)
            meta_s = self.f_small.render(meta, True, INK_500)
            self.screen.blit(name_s, (r.left + 10, r.top + 6))
            self.screen.blit(meta_s, (r.left + 10, r.top + 6 + name_s.get_height()))
            self._sugg_rects.append(r)

        if total > max_show:
            track = pygame.Rect(drop.right - 10, drop.top + 10, 6, drop_h - 20)
            pygame.draw.rect(self.screen, (235, 235, 235), track, border_radius=3)
            thumb_h = max(24, int(track.height * (max_show / total)))
            max_start = total - max_show
            thumb_y = int(track.top + (track.height - thumb_h) * (self.sugg_scroll_idx / max_start)) if max_start else track.top
            pygame.draw.rect(self.screen, (200, 200, 200), pygame.Rect(track.left, thumb_y, track.width, thumb_h), border_radius=3)
            self._suggest_track_rect = track
        else:
            self._suggest_track_rect = None

        self._suggest_drop_rect = drop

    def _draw_game_over(self):
        if not getattr(self.game, 'game_over', False):
            return

        sw, sh = self.screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0,0,0,150))
        self.screen.blit(overlay, (0,0))

        modal_w = 560
        modal_h = 260
        mx = (sw - modal_w)//2
        my = (sh - modal_h)//2
        modal = pygame.Rect(mx, my, modal_w, modal_h)
        pygame.draw.rect(self.screen, (255,255,255), modal, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, modal, 2, border_radius=12)

        if getattr(self.game, 'won', False):
            title = "Congratulations!"
            sub = f"You guessed {self.game.correct_country.name} in {len(self.game.guesses)} attempts."
            color = GREEN
        else:
            title = "Game Over"
            sub = f"The country was: {self.game.correct_country.name}"
            color = RED

        title_s = self.f_sub.render(title, True, color)
        self.screen.blit(title_s, (modal.centerx - title_s.get_width()//2, my + 28))
        sub_s = self.f_small.render(sub, True, INK_700)
        self.screen.blit(sub_s, (modal.centerx - sub_s.get_width()//2, my + 70))

        btn_w = 160
        btn_h = 44
        restart = pygame.Rect(modal.left + 80, modal.bottom - 80, btn_w, btn_h)
        quitb = pygame.Rect(modal.right - 80 - btn_w, modal.bottom - 80, btn_w, btn_h)
        pygame.draw.rect(self.screen, GREEN if getattr(self.game, 'won', False) else TEAL, restart, border_radius=8)
        pygame.draw.rect(self.screen, GRAY, quitb, border_radius=8)
        rtxt = self.f_button.render("PLAY AGAIN", True, WHITE)
        qtxt = self.f_button.render("QUIT", True, WHITE)
        self.screen.blit(rtxt, (restart.centerx - rtxt.get_width()//2, restart.centery - rtxt.get_height()//2))
        self.screen.blit(qtxt, (quitb.centerx - qtxt.get_width()//2, quitb.centery - qtxt.get_height()//2))

        self._restart_rect = restart
        self._quit_rect = quitb

    def _try_submit(self):
        if getattr(self.game, "game_over", False):
            return
        if self.game.suggestions and 0 <= self.game.selected_suggestion < len(self.game.suggestions):
            selected = self.game.suggestions[self.game.selected_suggestion]
            if self.game.make_guess(selected):
                self.game.current_input = ""
                self.game.suggestions = []
                self.game.selected_suggestion = 0
        else:
            if getattr(self.game, "current_input", ""):
                if self.game.make_guess(self.game.current_input):
                    self.game.current_input = ""
                    self.game.suggestions = []
                    self.game.selected_suggestion = 0

def enhance():
    game = GeodleGame()
    try:
        names = list(game.database.countries.keys())
        import random
        chosen = random.choice(names) if names else None
        game.correct_country = game.database.countries.get(chosen) if chosen else game.database.get_country_of_day()
    except Exception:
        game.correct_country = game.database.get_country_of_day()
    game.current_input = ""
    game.suggestions = []
    game.selected_suggestion = 0
    return game


def main():
    import pygame
    import sys
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Geodle")
    clock = pygame.time.Clock()
    
    game = enhance()
    ui = UI(screen, game)
    print(f"\nToday's country: {game.correct_country.name}")
    print("\nGame started! Good luck!\n")
    
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
                    if hasattr(ui, "handle_mouse"):
                        ui.handle_mouse(event)

                if event.type == pygame.KEYDOWN:
                    if not hasattr(game, "current_input"): game.current_input = ""
                    if not hasattr(game, "suggestions"): game.suggestions = []
                    if not hasattr(game, "selected_suggestion"): game.selected_suggestion = 0

                    if game.game_over:
                        if event.key == pygame.K_SPACE:
                            # Restart game
                            game = enhance()
                            ui.game = game
                            print(f"\nToday's country: {game.correct_country.name}")
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                    else:
                        if event.key == pygame.K_RETURN:
                            # Submit guess
                            if game.suggestions and 0 <= game.selected_suggestion < len(game.suggestions):
                                selected = game.suggestions[game.selected_suggestion]
                                if game.make_guess(selected):
                                    print(f"Guessed: {selected}")
                                    game.current_input = ""
                                    game.suggestions = []
                                    game.selected_suggestion = 0
                            elif game.current_input:
                                if game.make_guess(game.current_input):
                                    print(f"Guessed: {game.current_input}")
                                    game.current_input = ""
                                    game.suggestions = []
                                    game.selected_suggestion = 0
                        
                        elif event.key == pygame.K_BACKSPACE:
                            game.current_input = game.current_input[:-1]
                            game.suggestions = game.database.search_countries(game.current_input) if game.current_input else []
                            game.selected_suggestion = 0
                        
                        elif event.key == pygame.K_DOWN:
                            if game.suggestions:
                                game.selected_suggestion = (game.selected_suggestion + 1) % len(game.suggestions)
                        
                        elif event.key == pygame.K_UP:
                            if game.suggestions:
                                game.selected_suggestion = (game.selected_suggestion - 1) % len(game.suggestions)
                        
                        elif event.key == pygame.K_ESCAPE:
                            game.current_input = ""
                            game.suggestions = []
                        
                        else:
                            ch = getattr(event, "unicode", "")
                            if ch and ch.isprintable():
                                game.current_input += ch
                                game.suggestions = game.database.search_countries(game.current_input)
                                game.selected_suggestion = 0

            game.update()
        
            ui.render()
            pygame.display.flip()
            clock.tick(FPS)
    except Exception as e:
        import traceback
        traceback.print_exc()
        running = False
    finally:
        pygame.quit()
        try:
            sys.exit(0)
        except SystemExit:
            pass


if __name__ == "__main__":
    main()
