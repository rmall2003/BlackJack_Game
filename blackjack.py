import pygame
import random
import os
import json
import time

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 100
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
RED = (255, 0, 0)
BUTTON_COLOR = (70, 130, 180)
FONT = pygame.font.Font(None, 20)
# CHANGE: Added a medium font and reduced the large font size for better scaling.
FONT_MEDIUM = pygame.font.Font(None, 28)
FONT_LARGE = pygame.font.Font(None, 32)
CARD_WIDTH, CARD_HEIGHT = 100, 140
PLAYER_DATA_FILE = "player_data.json"
HIGHLIGHT_COLOR = (255, 215, 0)
DECK_POS = (WIDTH - CARD_WIDTH - 50, 50)
ANIMATION_SPEED_MS = 400

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Black Jack")
clock = pygame.time.Clock()

# Load background images from the 'assets' folder
try:
    MAIN_MENU_BG = pygame.image.load(os.path.join("assets", "main_page_bg.jpg")).convert()
    MAIN_MENU_BG = pygame.transform.scale(MAIN_MENU_BG, (WIDTH, HEIGHT))
    GAME_BG = pygame.image.load(os.path.join("assets", "game_page_bg.jpg")).convert()
    GAME_BG = pygame.transform.scale(GAME_BG, (WIDTH, HEIGHT))
except pygame.error:
    MAIN_MENU_BG = None
    GAME_BG = None

# Create a semi-transparent overlay
OVERLAY = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
OVERLAY.fill((0, 0, 0, 150))

# Load card images
def load_card_images(resized_width=100, resized_height=140):
    card_images = {}
    suits = ['hearts', 'diamonds', 'clubs', 'spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
    for suit in suits:
        for rank in ranks:
            filepath = os.path.join("assets", f"{rank}_of_{suit}.png")
            try:
                card_image = pygame.image.load(filepath).convert_alpha()
                card_image_resized = pygame.transform.scale(card_image, (resized_width, resized_height))
                card_images[f"{rank}_of_{suit}"] = card_image_resized
            except pygame.error:
                print(f"Warning: Could not load card image {filepath}")
                placeholder = pygame.Surface((resized_width, resized_height))
                placeholder.fill(WHITE)
                card_images[f"{rank}_of_{suit}"] = placeholder
    return card_images

CARD_IMAGES = load_card_images()
try:
    CARD_BACK = pygame.image.load(os.path.join("assets", "card_back.jpeg")).convert_alpha()
    CARD_BACK = pygame.transform.scale(CARD_BACK, (CARD_WIDTH, CARD_HEIGHT))
except pygame.error:
    CARD_BACK = pygame.Surface((CARD_WIDTH, CARD_HEIGHT)); CARD_BACK.fill(RED)


# Classes
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.image = CARD_IMAGES.get(f"{rank}_of_{suit}")

    def value(self):
        if self.rank.isdigit():
            return int(self.rank)
        elif self.rank in ['jack', 'queen', 'king']:
            return 10
        elif self.rank == 'ace':
            return 11

class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in ['hearts', 'diamonds', 'clubs', 'spades']
                      for rank in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']]
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.stopped = False
        self.is_dealer = name == "Dealer"
        self.show_second_card = False
        self.blackjack = False
        self.balance = 20000
        self.history = []

    def hit(self, card):
        self.hand.append(card)
        if self.calculate_score() == 21 and len(self.hand) >= 2:
            self.blackjack = True

    def calculate_score(self):
        score, aces = 0, 0
        for card in self.hand:
            value = card.value()
            if card.rank == 'ace':
                aces += 1
            score += value
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score

    def load_data(self, username):
        player_data = load_player_data(username)
        self.balance = player_data["balance"]
        self.history = player_data["history"]

    def save_data(self, username):
        player_data = {"balance": self.balance, "history": self.history}
        save_player_data(username, player_data)

# Button Class
class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action

    def draw(self, surface):
        pygame.draw.rect(surface, BUTTON_COLOR, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        text_surface = FONT.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.action:
                self.action()

# Game Functions
def get_player_card_pos(all_players, player_idx, card_idx, current_player_idx, dealer_is_playing, scroll_offset):
    y_pos = 50 - scroll_offset
    for i in range(player_idx):
        is_current = (i == current_player_idx and not dealer_is_playing)
        is_active_dealer = (all_players[i].is_dealer and dealer_is_playing)
        y_pos += 30 if not (is_current or is_active_dealer) else 40
        y_pos += CARD_HEIGHT + 50
    
    player = all_players[player_idx]
    is_current = (player_idx == current_player_idx and not dealer_is_playing)
    is_active_dealer = (player.is_dealer and dealer_is_playing)
    y_pos += 30 if not (is_current or is_active_dealer) else 40

    x_pos = 50 + card_idx * (CARD_WIDTH + 10)
    return x_pos, y_pos

def animate_card_deal(game_state, card, start_pos, end_pos):
    start_time = time.time()
    while True:
        elapsed_time = (time.time() - start_time) * 1000
        if elapsed_time >= ANIMATION_SPEED_MS:
            break
        
        progress = elapsed_time / ANIMATION_SPEED_MS
        current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
        current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress

        draw_table(
            game_state['all_players'],
            game_state['current_player_idx'],
            game_state['scroll_offset'],
            game_state['dealer_is_playing'],
            game_state.get('mouse_pos', (0,0))
        )
        screen.blit(card.image, (current_x, current_y))
        pygame.display.flip()
        clock.tick(FPS)

def draw_table(players, current_player_idx, scroll_offset, dealer_is_playing, mouse_pos=(0,0)):
    if GAME_BG:
        screen.blit(GAME_BG, (0, 0))
        screen.blit(OVERLAY, (0, 0))
    else:
        screen.fill(GREEN)

    y_offset = 50 - scroll_offset

    screen.blit(CARD_BACK, DECK_POS)
    deck_text = FONT.render("DECK", True, WHITE)
    deck_text_rect = deck_text.get_rect(center=(DECK_POS[0] + CARD_WIDTH / 2, DECK_POS[1] + CARD_HEIGHT + 15))
    screen.blit(deck_text, deck_text_rect)

    for idx, player in enumerate(players):
        is_current_player = (idx == current_player_idx and not dealer_is_playing)
        is_active_dealer = (player.is_dealer and dealer_is_playing)

        color = HIGHLIGHT_COLOR if is_current_player or is_active_dealer else WHITE
        # CHANGE: Use FONT_MEDIUM for the highlighted player's text
        font = FONT_MEDIUM if is_current_player or is_active_dealer else FONT
        blackjack_text = " - Black Jack!!" if player.blackjack else ""
        
        display_text = ""
        if player.is_dealer:
            score_val = player.hand[0].value() if player.hand and not player.show_second_card else player.calculate_score()
            display_text = f"{player.name} - Score: {score_val}{blackjack_text}"
        else:
            bet_text = f" | Bet: {getattr(player, 'bet', 0)}"
            balance_text = f" | Balance: {getattr(player, 'balance', 0)}"
            display_text = f"{player.name} - Score: {player.calculate_score()}{blackjack_text}{bet_text}{balance_text}"

        text = font.render(display_text, True, color)
        text_rect = text.get_rect(topleft=(50, y_offset))
        screen.blit(text, text_rect)
        
        x_card_offset = 50
        # CHANGE: Adjusted card y_offset to account for the new medium font size
        y_card_offset = y_offset + (35 if is_current_player or is_active_dealer else 30)

        # Logic to show player history on hover
        if not player.is_dealer and text_rect.collidepoint(mouse_pos):
            history_summary = []
            for record in player.history[-5:]:
                result_str = record.get("result", "N/A")
                if "Won" in result_str or "Lost" in result_str:
                    parts = result_str.split()
                    action = parts[-2]
                    amount = parts[-1]
                    history_summary.append(f"{action} {amount}")
                elif "Push" in result_str:
                    history_summary.append("Push")
            
            if history_summary:
                rendered_lines = [FONT.render(line, True, BLACK) for line in history_summary]
                max_width = max(line.get_width() for line in rendered_lines) if rendered_lines else 0
                box_height = len(rendered_lines) * 20 + 10
                box_width = max_width + 10
                
                # CHANGE: Position the tooltip box ABOVE the player's name text
                tooltip_x = text_rect.left
                tooltip_y = text_rect.top - box_height - 5  # 5 pixels of space
                
                # Prevent tooltip from going off-screen
                if tooltip_y < 0:
                    tooltip_y = text_rect.bottom + 5

                tooltip_box = pygame.Rect(tooltip_x, tooltip_y, box_width, box_height)
                pygame.draw.rect(screen, WHITE, tooltip_box)
                pygame.draw.rect(screen, BLACK, tooltip_box, 1)

                line_y_offset = tooltip_y + 5
                for line_surface in rendered_lines:
                    screen.blit(line_surface, (tooltip_x + 5, line_y_offset))
                    line_y_offset += 20
        
        for card_idx, card in enumerate(player.hand):
            if player.is_dealer and card_idx == 1 and not player.show_second_card:
                screen.blit(CARD_BACK, (x_card_offset, y_card_offset))
            else:
                if card.image:
                    screen.blit(card.image, (x_card_offset, y_card_offset))
            x_card_offset += CARD_WIDTH + 10
        
        y_offset = y_card_offset + CARD_HEIGHT + 20

def main_game_loop(multiplayer=False, usernames=None):
    running = True
    scroll_offset = 0
    dealer_played = False
    end_game = False
    dealer_is_playing = False

    players = [Player(name) for name in usernames]
    dealer = Player("Dealer")
    all_participants = players + [dealer]

    for player in players:
        player.load_data(player.name)

    deck = Deck()
    current_player_idx = 0

    for player in players:
        player.bet = get_bet(player.balance, player.name)
    
    mouse_pos = (0,0)
    game_state = {
        'all_players': all_participants,
        'current_player_idx': current_player_idx,
        'scroll_offset': scroll_offset,
        'dealer_is_playing': dealer_is_playing,
        'mouse_pos': mouse_pos
    }

    for i in range(2):
        for p_idx, player in enumerate(all_participants):
            new_card = deck.draw()
            if new_card:
                end_pos = get_player_card_pos(all_participants, p_idx, len(player.hand), current_player_idx, dealer_is_playing, scroll_offset)
                animate_card_deal(game_state, new_card, DECK_POS, end_pos)
                player.hit(new_card)

    for player in players:
        if player.calculate_score() == 21:
            player.blackjack = True

    def player_hit():
        nonlocal current_player_idx
        player = players[current_player_idx]
        if not player.stopped and player.calculate_score() < 21:
            new_card = deck.draw()
            if new_card:
                end_pos = get_player_card_pos(all_participants, current_player_idx, len(player.hand), current_player_idx, dealer_is_playing, scroll_offset)
                animate_card_deal(game_state, new_card, DECK_POS, end_pos)
                player.hit(new_card)
            if player.calculate_score() >= 21:
                player.stopped = True
                if len(players) > 1:
                    current_player_idx = (current_player_idx + 1) % len(players)

    def player_stop():
        nonlocal current_player_idx
        players[current_player_idx].stopped = True
        if len(players) > 1:
            current_player_idx = (current_player_idx + 1) % len(players)

    def trigger_end_game():
        nonlocal end_game
        end_game = True

    hit_button = Button(WIDTH - 150, HEIGHT - 100, 100, 50, "Hit", player_hit)
    stop_button = Button(WIDTH - 150, HEIGHT - 40, 100, 50, "Stop", player_stop)
    end_game_button = Button(WIDTH // 2 - 50, HEIGHT - 60, 100, 40, "End Game", trigger_end_game)

    while running:
        clock.tick(FPS)
        all_players_stopped = all(p.stopped for p in players)
        
        mouse_pos = pygame.mouse.get_pos()
        game_state['current_player_idx'] = current_player_idx
        game_state['dealer_is_playing'] = dealer_is_playing
        game_state['mouse_pos'] = mouse_pos

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if not all_players_stopped:
                hit_button.handle_event(event)
                stop_button.handle_event(event)
            if dealer_played:
                end_game_button.handle_event(event)
        
        if not all_players_stopped:
            while players[current_player_idx].stopped and not all(p.stopped for p in players):
                current_player_idx = (current_player_idx + 1) % len(players)

        if all_players_stopped and not dealer_played:
            if not dealer_is_playing:
                dealer_is_playing = True
                dealer.show_second_card = True
            
            dealer_must_hit = dealer.calculate_score() < 17 or \
                              (dealer.calculate_score() == 17 and any(c.rank == 'ace' for c in dealer.hand))
            
            if dealer_must_hit:
                pygame.time.wait(400) # Pause to make dealer's turn visible
                new_card = deck.draw()
                if new_card:
                    end_pos = get_player_card_pos(all_participants, len(players), len(dealer.hand), current_player_idx, True, scroll_offset)
                    animate_card_deal(game_state, new_card, DECK_POS, end_pos)
                    dealer.hit(new_card)
            else:
                if dealer.calculate_score() == 21 and len(dealer.hand) == 2:
                    dealer.blackjack = True
                dealer_played = True

        draw_table(all_participants, current_player_idx, scroll_offset, dealer_is_playing, mouse_pos)
        if not all_players_stopped:
            hit_button.draw(screen)
            stop_button.draw(screen)
        
        if dealer_played:
            end_game_button.draw(screen)

        pygame.display.flip()

        if end_game and dealer_played:
            running = False

    dealer_score = dealer.calculate_score()
    results = []
    for player in players:
        player_score = player.calculate_score()
        res_text = ""
        if player_score > 21:
            player.balance -= player.bet
            res_text = f"Bust! Lost {player.bet}"
        elif dealer.blackjack and not player.blackjack:
             player.balance -= player.bet
             res_text = f"Dealer Black Jack! Lost {player.bet}"
        elif dealer_score > 21 or player_score > dealer_score:
            win_amount = int(player.bet * 1.5) if player.blackjack else player.bet
            player.balance += win_amount
            res_text = f"{'Black Jack! ' if player.blackjack else ''}Won {win_amount}"
        elif player_score == dealer_score:
            if player.blackjack and not dealer.blackjack:
                win_amount = int(player.bet * 1.5)
                player.balance += win_amount
                res_text = f"Black Jack! Won {win_amount}"
            else:
                res_text = "Push"
        else:
            player.balance -= player.bet
            res_text = f"Lost {player.bet}"
        
        player.history.append({"bet": player.bet, "result": res_text, "balance": player.balance})
        player.save_data(player.name.split(" (Split)")[0])
        results.append((player.name, f"{player_score} | {res_text} | Balance: {player.balance}"))
    
    results.append(("Dealer", f"Score: {dealer_score}"))

    show_results = True
    def go_to_menu(): nonlocal show_results; show_results = False
    def quit_game(): pygame.quit(); exit()

    button_width, button_spacing = 120, 20
    total_buttons_width = button_width * 2 + button_spacing
    start_x = (WIDTH - total_buttons_width) / 2
    menu_button = Button(start_x, HEIGHT - 100, button_width, 50, "Main Menu", go_to_menu)
    exit_button = Button(start_x + button_width + button_spacing, HEIGHT - 100, button_width, 50, "Exit", quit_game)

    while show_results:
        if GAME_BG: screen.blit(GAME_BG, (0, 0)); screen.blit(OVERLAY, (0, 0))
        else: screen.fill(BLACK)
        
        y_res_offset = 100
        for name, result in results:
            # CHANGE: Use FONT_MEDIUM for the results screen for consistency
            text = FONT_MEDIUM.render(f"{name}: {result}", True, WHITE)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y_res_offset))
            y_res_offset += 50
        
        menu_button.rect.top = y_res_offset + 20
        exit_button.rect.top = y_res_offset + 20
        menu_button.draw(screen)
        exit_button.draw(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: quit_game()
            menu_button.handle_event(event)
            exit_button.handle_event(event)

# Player Data Functions
def get_all_usernames():
    if not os.path.exists(PLAYER_DATA_FILE): return []
    with open(PLAYER_DATA_FILE, "r") as f:
        try: data = json.load(f); return list(data.keys())
        except json.JSONDecodeError: return []

def load_player_data(username):
    if not os.path.exists(PLAYER_DATA_FILE): return {"balance": 20000, "history": []}
    with open(PLAYER_DATA_FILE, "r") as f:
        try: data = json.load(f)
        except json.JSONDecodeError: data = {}
    return data.get(username, {"balance": 20000, "history": []})

def save_player_data(username, player_data):
    data = {}
    if os.path.exists(PLAYER_DATA_FILE):
        with open(PLAYER_DATA_FILE, "r") as f:
            try: data = json.load(f)
            except json.JSONDecodeError: pass
    data[username] = player_data
    with open(PLAYER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Utility functions
def get_usernames(num_players):
    usernames = []
    current_input = ""
    existing_users = get_all_usernames()

    for i in range(num_players):
        active = True
        while active:
            if GAME_BG: screen.blit(GAME_BG, (0, 0)); screen.blit(OVERLAY, (0, 0))
            else: screen.fill(BLACK)

            prompt = FONT.render(f"Player {i+1}, enter username (letters only, max 10): {current_input}", True, WHITE)
            screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2 - 40))

            if existing_users:
                user_list_text = FONT.render("Existing Users: " + ", ".join(existing_users), True, WHITE)
                screen.blit(user_list_text, (WIDTH // 2 - user_list_text.get_width() // 2, HEIGHT - 60))

            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and current_input:
                        usernames.append(current_input.lower())
                        current_input = ""
                        active = False
                    elif event.key == pygame.K_BACKSPACE:
                        current_input = current_input[:-1]
                    elif len(current_input) < 10 and event.unicode.isalpha():
                        current_input += event.unicode
    return usernames

def get_number_of_players():
    num_players_str = ""
    while True:
        if GAME_BG: screen.blit(GAME_BG, (0, 0)); screen.blit(OVERLAY, (0, 0))
        else: screen.fill(BLACK)

        prompt = FONT.render(f"Enter number of players (2-6): {num_players_str}", True, WHITE)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and num_players_str.isdigit() and 2 <= int(num_players_str) <= 6:
                    return int(num_players_str)
                elif event.key == pygame.K_BACKSPACE:
                    num_players_str = num_players_str[:-1]
                elif event.unicode.isdigit():
                    num_players_str += event.unicode

def get_bet(player_balance, player_name):
    bet_input = ""
    while True:
        if GAME_BG: screen.blit(GAME_BG, (0, 0)); screen.blit(OVERLAY, (0, 0))
        else: screen.fill(BLACK)

        prompt_text = f"{player_name} | Balance: {player_balance} | Enter your bet: {bet_input}"
        prompt = FONT.render(prompt_text, True, WHITE)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and bet_input.isdigit() and 1 <= int(bet_input) <= player_balance:
                    return int(bet_input)
                elif event.key == pygame.K_BACKSPACE:
                    bet_input = bet_input[:-1]
                elif event.unicode.isdigit() and len(bet_input) < 7:
                    bet_input += event.unicode

# Main Menu
def main_menu():
    running = True
    while running:
        if MAIN_MENU_BG:
            screen.blit(MAIN_MENU_BG, (0, 0))
            screen.blit(OVERLAY, (0, 0))
        else:
            screen.fill(BLACK)

        title_text = FONT_LARGE.render("Black Jack Game", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

        single_player_text = FONT.render("Press [1] for Single Player", True, WHITE)
        screen.blit(single_player_text, (WIDTH // 2 - single_player_text.get_width() // 2, HEIGHT // 2 - 30))

        multiplayer_text = FONT.render("Press [2] for Multiplayer", True, WHITE)
        screen.blit(multiplayer_text, (WIDTH // 2 - multiplayer_text.get_width() // 2, HEIGHT // 2 + 30))

        quit_text = FONT.render("Press [ESC] to Quit", True, WHITE)
        screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 90))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    usernames = get_usernames(1)
                    if usernames: main_game_loop(multiplayer=False, usernames=usernames)
                elif event.key == pygame.K_2:
                    num_players = get_number_of_players()
                    if num_players:
                        usernames = get_usernames(num_players)
                        if usernames: main_game_loop(multiplayer=True, usernames=usernames)

# Entry Point
if __name__ == "__main__":
    main_menu()
    pygame.quit()