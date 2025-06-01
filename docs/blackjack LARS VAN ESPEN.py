import copy     # Importeert de copy-module zodat we copy.deepcopy kunnen gebruiken – daarmee
                 # maken we een volledig onafhankelijke kloon van een lijst, wat noodzakelijk
                 # is om het “master deck” te beschermen wanneer we straks met meerdere decks
                 # gaan schudden en kaarten uitdelen.
import random   # Bevat de random-functionaliteit om willekeurige getallen (en dus kaarten)
                # te kiezen tijdens het delen.
import pygame   # Laadt de volledige Pygame-bibliotheek, die alle functionaliteit voor het
                # venster, tekenen, geluid, fonts, events, enz. bevat.

#Pygame opstarten & globale variabelen initialiseren

pygame.init()   # Initialiseert ALLE interne subsystemen van Pygame (video, audio, font...).
                # Dit moet altijd precies één keer helemaal bovenaan elk Pygame-programma
                # staan voordat je functies van Pygame gebruikt

cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']  # Waarden van één
                                                                            # kleur/soort; als strings zodat we later makkelijk ‘J’, ‘Q’, ‘K’ en ‘A’
                                                                            # kunnen herkennen.
one_deck = 4 * cards    # Eén standaard deck telt 4 keer elke waarde (♠♥♦♣).
DECKS = 4               # Aantal decks waarmee we tegelijk spelen (Blackjack-tafels in casino’s gebruiken meestal 4–8).

WIDTH, HEIGHT = 600, 900    # Breedte van het venster in pixels.
FPS = 60                    # FPS zodat game niet crasht

screen = pygame.display.set_mode([WIDTH, HEIGHT])   # Maakt een venster met bovenstaande
                                                    # resolutie en geeft het Surface-object
                                                    # terug waarop we alles tekenen.

pygame.display.set_caption('Pygame Blackjack!') # Zet de titel in de titelbalk.
clock = pygame.time.Clock()                     # Clock-object waarmee we het tempo kunnen begrenzen
                                                # en tijd sinds vorige frame kunnen meten.
font = pygame.font.Font('freesansbold.ttf', 44) # Groot font (44 px) voor kaarten, tekst.
small_font = pygame.font.Font('freesansbold.ttf', 32) # Iets kleiner font (36 px) voor scores.

active = False              # Wordt True zodra er een hand gedeeld is
initial_deal = False        # Wordt True vlak nadat op DEAL HAND geklikt wordt; zorgt ervoor
                            # dat er precies één keer twee kaarten aan allebei gedeeld worden.
                         
hand_active = False         # True zolang speler nog HIT kan kiezen (dus voor Stand / bust).
reveal_dealer = False       # Wordt True zodra speler stand kiest of bust; toont tweede
                            # dealerkaart en laat dealer spelen.
add_score = False           
                         

player_hand, dealer_hand = [], []
player_score = dealer_score = 0

game_deck = []

records = [0, 0, 0]         # Telt [wins, losses, draws] over alle gespeelde handen.
results_txt = ['', '', '', '', '']

action_outcome = 0

punishments = ['push-ups', 'sit-ups', 'squats']
punishment_choice = ''
outcome_shown = False
outcome_timer = 0
WAIT_TIME = 2000

#Hulpfuncties 

def deal_cards(current_hand, current_deck):
    """Trekt 1 willekeurige kaart uit current_deck en stopt die in current_hand.
       Geeft (hand, deck) terug zodat we de aangepaste lijsten direct kunnen terug gebruiken."""
    idx = random.randrange(len(current_deck))
    current_hand.append(current_deck.pop(idx))
    return current_hand, current_deck


def calculate_score(hand):
    """Berekent de best mogelijke Blackjack-score voor een gegeven hand.
       Azen tellen eerst als 11; daarna verlagen we ze tot 1 zolang dat nodig is
       om onder (of gelijk aan) 21 te blijven."""
    score = 0
    aces = hand.count('A')
    for card in hand:
        if card in cards[:8]:
            score += int(card)
        elif card in ['10', 'J', 'Q', 'K']:
            score += 10
        else:
            score += 11
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score


def draw_scores(p_score, d_score):
    """Tekent de (tijdelijke) score van speler en – als reveal_dealer True is – van de dealer."""
    screen.blit(font.render(f'Score[{p_score}]', True, 'white'), (350, 400))
    if reveal_dealer:
        screen.blit(font.render(f'Score[{d_score}]', True, 'white'), (350, 100))


def draw_cards(player, dealer):
    """Tekent alle kaarten van speler en dealer als simple rectangles met witte achtergrond
       en rode/ blauwe rand. Dealer verbergt de eerste kaart zolang reveal False is."""
    for i, card in enumerate(player): #bv: player = ["harten 10", "klaver vrouw", "ruiten aas"]
                                            #for i, card in enumerate(player):
                                            #print(f"Kaart {i}: {card}")

        x, y = 70 + 70 * i, 460 + 5 * i
        pygame.draw.rect(screen, 'white', [x, y, 120, 220], 0, 5)
        for o in (0, 170):
            screen.blit(font.render(card, True, 'black'), (x + 5, y + 5 + o))
        pygame.draw.rect(screen, 'red', [x, y, 120, 220], 5, 5)
    for i, card in enumerate(dealer):
        x, y = 70 + 70 * i, 160 + 5 * i
        pygame.draw.rect(screen, 'white', [x, y, 120, 220], 0, 5)
        if i != 0 or reveal_dealer:
            for o in (0, 170):
                screen.blit(font.render(card, True, 'black'), (x + 5, y + 5 + o))
        else:
            for o in (0, 170):
                screen.blit(font.render('???', True, 'black'), (x + 5, y + 5 + o))
        pygame.draw.rect(screen, 'blue', [x, y, 120, 220], 5, 5)


def render_multiline(text, font_obj, color, max_width):
    words = text.split(' ')
    lines = []
    line = ''
    for w in words:
        test = line + (' ' if line else '') + w
        if font_obj.size(test)[0] <= max_width:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    surfaces = [font_obj.render(l, True, color) for l in lines]
    return surfaces


def draw_overlay(message):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    rect = pygame.Rect(20, 200, 560, 300)
    pygame.draw.rect(screen, 'white', rect, 0, 10)
    lines = render_multiline(message, small_font, 'black', rect.width - 40)
    start_y = rect.centery - (len(lines) * (small_font.get_height() + 10)) // 2
    for s in lines:
        s_rect = s.get_rect(center=(rect.centerx, start_y))
        screen.blit(s, s_rect)
        start_y += small_font.get_height() + 10
    button_rect = pygame.Rect(rect.centerx - 150, rect.bottom - 110, 300, 80)
    pygame.draw.rect(screen, 'green', button_rect, 0, 10)
    txt_surface = font.render('NEW HAND', True, 'black')
    txt_rect = txt_surface.get_rect(center=button_rect.center)
    screen.blit(txt_surface, txt_rect)
    return button_rect


def draw_game_ui(result_code):
    btns = []
    if result_code:
        btns.append(('new', draw_overlay(results_txt[result_code])))
        return btns
    if not active:
        deal_rect = pygame.draw.rect(screen, 'white', [150, 20, 300, 100], 0, 5)
        pygame.draw.rect(screen, 'green', [150, 20, 300, 100], 3, 5)
        screen.blit(font.render('DEAL HAND', True, 'black'), (165, 50))
        btns.append(('deal', deal_rect))
    else:
        hit_rect = pygame.draw.rect(screen, 'white', [0, 700, 300, 100], 0, 5)
        pygame.draw.rect(screen, 'green', [0, 700, 300, 100], 3, 5)
        screen.blit(font.render('HIT ME', True, 'black'), (55, 735))
        btns.append(('hit', hit_rect))
        stand_rect = pygame.draw.rect(screen, 'white', [300, 700, 300, 100], 0, 5)
        pygame.draw.rect(screen, 'green', [300, 700, 300, 100], 3, 5)
        screen.blit(font.render('STAND', True, 'black'), (355, 735))
        btns.append(('stand', stand_rect))
        record = small_font.render(f'Wins: {records[0]}   Losses: {records[1]}   Draws: {records[2]}', True, 'white')
        screen.blit(record, (15, 840))
    return btns


def check_endgame(deal_score, play_score):
    """Controleert of de hand klaar is (speler heeft stand of is bust) en
       dealer heeft ten minste 17. Bepaalt dan de uitkomst en werkt het
       win-/verlies-/gelijkspel-totaal precies 1 keer bij."""
    if not hand_active and deal_score >= 17:
        if play_score > 21:
            return 1
        if deal_score < play_score <= 21 or deal_score > 21:
            return 2
        if play_score < deal_score <= 21:
            return 3
        return 4
    return 0

# Hoofd-gameloop
run = True
while run:
    clock.tick(FPS)                 # 60 fps aanhouden.
    screen.fill('black')            # Maak scherm leeg (zwarte achtergrond).

#intitial_deal start als False, en wordt verder in deze loop naar True gezet
    if initial_deal: # Precisé één keer na ‘DEAL HAND’. 
        for _ in range(2): # Twee kaarten naar elk.
            player_hand, game_deck = deal_cards(player_hand, game_deck)
            dealer_hand, game_deck = deal_cards(dealer_hand, game_deck)
        initial_deal = False
    if active:# Spel is bezig? → kaarten & scores tekenen.
        player_score = calculate_score(player_hand)
        draw_cards(player_hand, dealer_hand)
        if reveal_dealer: # Dealer mag z’n hand afmaken.
            dealer_score = calculate_score(dealer_hand)
            if dealer_score < 17: # Dealer moet kaart trekken tot minimaal 17.
                dealer_hand, game_deck = deal_cards(dealer_hand, game_deck)
        draw_scores(player_score, dealer_score)
    if action_outcome and not outcome_shown:
        if outcome_timer == 0:
            outcome_timer = pygame.time.get_ticks()
            punishment_choice = random.choice(punishments)
        if pygame.time.get_ticks() - outcome_timer >= WAIT_TIME:
            outcome_shown = True
            if action_outcome in (1, 3):
                results_txt[action_outcome] = f'VERLOREN! Doe {player_score} {punishment_choice}.'
            elif action_outcome == 2:
                results_txt[action_outcome] = f'GEWONNEN! Kies iemand die {player_score} {punishment_choice} moet doen.'
            else:
                results_txt[action_outcome] = 'GELIJK SPEL!'
            active = False
    display_result = action_outcome if outcome_shown else 0
    ui_buttons = draw_game_ui(display_result)
    for event in pygame.event.get(): # Event-afhandeling.
        if event.type == pygame.QUIT: # Vensterkruisje → spel afsluiten.
            run = False
        elif event.type == pygame.MOUSEBUTTONUP: # Muisklik losgelaten
            for lbl, rect in ui_buttons:
                if rect.collidepoint(event.pos):
                    if lbl == 'deal':
                        active = True
                        initial_deal = True
                        reveal_dealer = False
                        hand_active = True
                        add_score = True
                        action_outcome = 0
                        outcome_shown = False
                        outcome_timer = 0
                        punishment_choice = ''
                        game_deck = copy.deepcopy(DECKS * one_deck) # Vers, geschud deck.
                        player_hand.clear()
                        dealer_hand.clear()
                        player_score = dealer_score = 0
                    elif lbl == 'hit' and player_score < 21 and hand_active: # Spel gaande → HIT / STAND / NEW HAND.
                        player_hand, game_deck = deal_cards(player_hand, game_deck)
                    elif lbl == 'stand': # Speler kiest STAND.
                        reveal_dealer = True
                        hand_active = False
                    elif lbl == 'new': # NEW HAND (na vorige hand klaar).
                        active = True
                        initial_deal = True
                        reveal_dealer = False
                        hand_active = True
                        add_score = True
                        action_outcome = 0
                        outcome_shown = False
                        outcome_timer = 0
                        punishment_choice = ''
                        dealer_score = player_score = 0
                        game_deck = copy.deepcopy(DECKS * one_deck)
                        player_hand.clear()
                        dealer_hand.clear()
    if hand_active and player_score >= 21:  # Speler bust tijdens eigen beurt.
        hand_active = False
        reveal_dealer = True # Dealer mag hand afmaken en we evalueren.
    if not outcome_shown:
        action_outcome = check_endgame(dealer_score, player_score)
        if action_outcome and add_score:
            if action_outcome in (1, 3):
                records[1] += 1
            elif action_outcome == 2:
                records[0] += 1
            elif action_outcome == 4:
                records[2] += 1
            add_score = False
    pygame.display.flip() 
pygame.quit() # Ruimt alle Pygame-subsystemen weer op.
