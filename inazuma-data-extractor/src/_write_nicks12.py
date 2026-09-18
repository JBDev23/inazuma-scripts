# -*- coding: utf-8 -*-
"""preferred_id -> nick(s) CSV en juego1/juego2 (pueden diferir entre juegos)."""

import json
from pathlib import Path

DATA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

# Solo entradas donde el ID preferido != nick CSV (o hay variantes entre juegos)
ALIASES = {
    # Brainwashing: juego1=Buster, juego2=Busta
    "Busta": ["Busta", "Buster"],
    # Umbrella: juego1=Scott, juego2=Mildford
    "Scott": ["Scott", "Mildford"],
    # Alpine Shawn Froste
    "Shawn": ["Froste", "Shawn"],
    # Royal Academy Redux Caleb Stonewall
    "Caleb": ["Stonewall", "Stonew’l", "Caleb"],
    # Fauxshore Darren LaChance
    "Darren": ["LaChance", "Darren"],
    # Mary Times Memorial
    "Rocky": ["Rocky", "Black"],
    "Hurley": ["Kane", "Hurley"],
    # Dark Emperors Malcolm Night — nick CSV es Night
    "Night": ["Night", "Malcolm"],
}

# Roster IE1+2 en orden del usuario (IDs preferidos, sin duplicar claves)
NICKS = """
Mark
Jack
Jim
Bobby
Tod
Nathan
Steve
Timmy
Sam
Jude
Max
Kevin
Axel
Willy
King
Carlton
Drent
Simmons
Martin
Master
Bloom
Swing
Waldon
Potts
Tomlinson
Ingham
Lawrenson
Samford
Hatch
Mask
Zombie
Styx
Franky
Undead
Creepy
Jiangshi
Mummy
Grave
Wolfy
Ghost
Blood
Dollman
Noir
Alien
Talisman
Boar
Bullford
Toad
Fishman
Raccoon
Lion
Monkey
Chameleon
Mouseman
Koala
Chicken
Eagle
Panda
Cheetah
Gorilla
Snake
Feldt
Under
Waters
Good
Stronger
Marvel
Leading
Stiller
Oughtry
Tell
Rock
Kind
Busta
Mooney
Seller
Turner
Idol
Eldorado
Train
Vox
Cosplay
Formby
Net
Hero
Signalman
Robot
Novel
Online
Custom
Gamer
Artist
Arcade
Hood
Castle
Bandit
Crackshot
Hopper
Hillfort
Thunder
Cleats
Spook
Trops
Star
Hattori
Code
Samurai
Ronin
Cloak
Greeny
Mower
Sherman
Hillvalley
Lively
Hayseed
Grower
Nevis
Work
Howells
Milky
Dawson
Spray
Mother
Roast
Muffs
Neville
Calier
Night
Clover
Meenan
Mirthful
Middleton
Wells
Moore
Damian
Nashmith
Gloom
Talis
Tyler
Thomas
Marvin
Icarus
Apollo
Hephestus
Ares
Dionysus
Heracles
Chronos
Artemis
Medusa
Hera
Hermes
Athena
Demeter
Achilles
Aphrodite
Ingram
Banker
Sefton
Caperock
Strike
Chops
Porter
Molehill
Most
Chaney
Rhymes
Tunk
Morefield
Scott
Cyborg
Hairtown
Steaky
MacHines
Foreman
Butler
Nathaniel
Suffolk
Tailor
Gladstone
Heart
Poe
Barista
Builder
Ropes
Peggs
Gleeson
Bindings
Downtown
Strata
Ursus
Bootgaiter
Maddox
Bogg
Skipolson
Snowfield
Onlign
Rackner
Climbstein
Shawn
Kik
Bookworm
Gami
Waxon
Maxi
Sparky
Water
Banyan
Dinglite
Telektual
Kandel
Fardream
Ation
Wando
Marshall
Dirk
Cellar
Healen
Bargie
Bamboo
Little
Beltzer
Color
Sparrow
Spark
Beck
Messer
Caleb
Wildhorse
Jamm
Daisy
Closeout
Brook
Pinkpetal
Greenland
Sand
Spires
Earth
Cash
Sunrise
Bush
Bluebells
Revel
Moor
Willow
Hartland
Darren
Cracker
Bathers
Badgame
Mishap
Leave
Fake
Duskplay
Random
Cotts
Richmen
Failing
Passing
Luckyman
Poker
Fate
Rocky
Cooley
Redding
Breakfast
Hills
Diver
Hurley
Contented
Griddle
Andagi
Fordline
Delight
Soundtown
Easton
Talent
Shark
Ironwall
Sights
Western
Stevens
Smith
Beray
Hammond
Safehouse
Firepool
Firsthand
Tappin
Agent M
Tori
Mirror
Kenneddy
Shadey
Galileo
Coral
Gigs
Ganymede
Charon
Pandora
Grengo
Io
Janus
Rihm
Diam
Dvalin
Kenville
Mole
Kayson
Tytan
Fedora
Krypto
Sworm
Mercury
Metron
Zell
Nero
Gele
Kiburn
Zohen
Hauser
Kormer
Kiwill
Ark
Wittz
Bellatrix
Xene
Grent
Baller
Balcke
Seats
Bomber
Heat
Lean
Bountine
Sidern
Torch
Neppten
Beluga
Arkew
Clear
Gocker
Icer
Balen
Droll
Rhine
Blown
Gazelle
Frost
Shadow
""".strip().splitlines()

# Nota: King/Samford/Feldt/Jim/... aparecen en varios equipos; una sola clave en el JSON.
# Night está una vez (Kirkwood + Dark Emperors comparten nick CSV "Night").
# Se omiten repeticiones de Raimon en Dark Emperors (mismo nick → mismos moves base).


def main():
    # Mantener orden, únicos
    seen = set()
    ordered = []
    for n in NICKS:
        n = n.strip()
        if n and n not in seen:
            seen.add(n)
            ordered.append(n)

    # Asegurar jugadores Dark Emperors que no están ya (Shadow es nuevo; resto ya en Raimon/Kirkwood)
    for extra in ["Shadow"]:
        if extra not in seen:
            ordered.append(extra)
            seen.add(extra)

    (DATA_RAW / "nicks.txt").write_text("\n".join(ordered) + "\n", encoding="utf-8")
    (DATA_RAW / "nicks_aliases.json").write_text(
        json.dumps(ALIASES, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote nicks.txt ({len(ordered)} unique)")
    print(f"Wrote nicks_aliases.json ({len(ALIASES)} aliases)")


if __name__ == "__main__":
    main()
