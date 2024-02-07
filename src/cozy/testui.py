from datetime import datetime
from typing import Callable, Tuple, Any

import PySimpleGUI as sg
from PySimpleGUI import Window, Element

from cozy.model.models import Site, Staff, Chair

site: Site = Site(capacity=25, name="Cozy", staff=[Staff(name="Alice"), Staff(name="Bob")], chairs=[Chair(id=1, occupant=None, since=None), Chair(id=2, occupant=None, since=None)])

while len(site.chairs) < site.capacity:
    site.chairs.append(Chair(id=len(site.chairs) + 1, occupant=None, since=None))

print(site.json())
sg.theme('DarkAmber')  # Add a touch of color
staff_button_list = [sg.Button(s.name) for s in site.staff]


# All the stuff inside your window.
def create_window() -> Window:
    layout = [
        staff_button_list,
        [
            sg.Button('Add new Staff', enable_events=True, key='AddNewStaff'),
            sg.Button('Add', enable_events=True, key='StaffAdd', visible=False),
            sg.Button('Woops!', enable_events=True, key='StaffCancelAdd', visible=False),
            sg.InputText(disabled=True, enable_events=True, key='StaffName', visible=False)
        ],

    ]

    layout.extend(create_chairs())

    # Create the Window
    return sg.Window('Window Title', layout)


def create_chairs() -> list[list[Element]]:
    chair_rows = []
    for c in site.chairs:
        chair_rows.append(create_single_chair(c))

    return chair_rows


def create_single_chair(chair: Chair) -> list[Element]:
    return [
        sg.Text(f'Chair {chair.id}'),
        sg.InputText(disabled=False, enable_events=False, key=f'Chair{chair.id}Occupant', visible=True, default_text=chair.occupant.name if chair.occupant else '', metadata=chair),
        sg.Checkbox('', enable_events=True, key=f'Chair{chair.id}Occupied', visible=True, default=chair.occupant is not None, metadata=chair),
        sg.Text(chair, key=f'Chair{chair.id}Since', visible=True, metadata=chair),
    ]


window = create_window()
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
        break
    print('You entered ', values)
    print(event)

    if event == 'AddNewStaff':
        print('AddNewStaff Button init')
        add_btn = window['AddNewStaff']
        do_add_btn = window['StaffAdd']
        cancel_add_btn = window['StaffCancelAdd']
        txt = window['StaffName']
        print('AddNewStaff : begin', txt.Disabled)
        add_btn.update(disabled=True, visible=False)
        txt.update(disabled=False, visible=True)
        do_add_btn.update(disabled=False, visible=True)
        cancel_add_btn.update(disabled=False, visible=True)

    if event == 'StaffAdd':
        add_btn = window['AddNewStaff']
        do_add_btn = window['StaffAdd']
        cancel_add_btn = window['StaffCancelAdd']
        txt = window['StaffName']
        print('AddNewStaff: Update')
        site.staff.append(Staff(name=values['StaffName']))
        staff_button_list = [sg.Button(s.name) for s in site.staff]
        window.close()
        window = create_window()

    if event == 'SeatCount':
        count = window['SeatCount']
        try:
            _c = int(values['SeatCount'])

            if _c < len(site.chairs) and site.chairs:
                print(f'SeatCount: Update -- removing chairs from site until count is {_c}')
                while len(site.chairs) > _c:
                    print(f'Seat count is {len(site.chairs)} > {_c}... removing one')
                    site.chairs.pop()
            elif _c > len(site.chairs):
                print(f'SeatCount: Update -- adding chairs to site until count is {_c}')
                while len(site.chairs) < _c:
                    site.chairs.append(Chair(id=len(site.chairs), occupant=None, since=None))
            window.close()
            window = create_window()
        except ValueError:
            pass

    if event in ['StaffCancelAdd']:
        add_btn = window['AddNewStaff']
        do_add_btn = window['StaffAdd']
        cancel_add_btn = window['StaffCancelAdd']
        txt = window['StaffName']
        add_btn.update(disabled=False, visible=True)
        txt.update(disabled=True, visible=False, value='')
        do_add_btn.update(disabled=True, visible=False)
        cancel_add_btn.update(disabled=True, visible=False)

    if event.startswith('Chair'):
        chair = window[event].metadata
        occupant = values[str(event).replace('Occupied', 'Occupant')]
        print(f'Chair {chair.id} is occupied: {values[event]}')
        if values[event]:
            chair.since = datetime.now()
            chair.occupant = occupant
        else:
            chair.occupant = None
            chair.since = None
        window[str(event).replace('Occupied', 'Since')].update(str(chair))
        window[str(event).replace('Occupied', 'Occupant')].update(str(chair.occupant if chair.occupant else ''))


window.close()
