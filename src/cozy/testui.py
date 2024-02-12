from datetime import datetime
from os.path import expanduser
from pathlib import Path

home = Path(expanduser("~"))

import PySimpleGUI as sg
from PySimpleGUI import Window, Element

from cozy.model.models import Site, Staff, Chair, Client

# site: Site = Site(capacity=25, name="Cozy", staff=[Staff(name="Alice"), Staff(name="Bob")], chairs=[Chair(id=1, occupant=None, since=None), Chair(id=2, occupant=None, since=None)])

# load the site from the default location :
cozy_home = home / '.cozy'
cozy_default_site_file = cozy_home / 'empty_site.json'
cozy_data_folder = cozy_home / 'data'
cozy_today_site_folder = cozy_home / 'data' / datetime.now().strftime('%Y-%m-%d')
cozy_today_site_file = cozy_today_site_folder / 'site_state.json'

if not cozy_home.exists():
    cozy_home.mkdir()

if not cozy_data_folder.exists():
    cozy_data_folder.mkdir()

if not cozy_default_site_file.exists():
    default_site: Site = Site(capacity=25, name="Cozy", staff=[], chairs=[])
    while len(default_site.chairs) < default_site.capacity:
        default_site.chairs.append(Chair(id=len(default_site.chairs) + 1, occupant=None, since=None))
    cozy_default_site_file.write_text(data=default_site.model_dump_json(indent=2), encoding='utf-8')
else:
    default_site: Site = Site.model_validate_json(cozy_default_site_file.read_text(encoding='utf-8'))

# now we load the actual site or take a copy of the default site
if not cozy_today_site_folder.exists():
    cozy_today_site_folder.mkdir()
    cozy_today_site_file.write_text(data=default_site.model_dump_json(indent=2), encoding='utf-8')

site: Site = Site.model_validate_json(cozy_today_site_file.read_text(encoding='utf-8'))

sg.theme('DarkAmber')  # Add a touch of color
staff_button_list = [sg.Button(s.name) for s in site.staff]


def save_staff():
    default_site.staff = [staff for staff in site.staff]
    cozy_default_site_file.write_text(data=default_site.model_dump_json(indent=2), encoding='utf-8')


def save_site():
    cozy_today_site_file.write_text(data=site.model_dump_json(indent=2), encoding='utf-8')


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
        save_staff()
        save_site()

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
            chair.occupant = Client.parse_obj({'name': occupant})
        else:
            chair.occupant = None
            chair.since = None
        window[str(event).replace('Occupied', 'Since')].update(str(chair))
        window[str(event).replace('Occupied', 'Occupant')].update(str(chair.occupant if chair.occupant else ''))
        save_site()


window.close()
