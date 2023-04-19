# Simarine: Camper Control & Pico to SignalK

Reads Simarine Camper Control & Pico config and values and insert them into SignalK

## Python to NodeJS

In progress of being converted to NodeJS.
Currently the config is still picked up by a python script (pico.py).
Afterwards, the UDP broadcast listening and update processing happens in NodeJS.


## Plugin options

You can set the start instances of batteries, tanks etc here.


## Start
python.exe -m pip install --upgrade pip
build
run npm -install