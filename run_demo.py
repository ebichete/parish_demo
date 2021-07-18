import streamlit as st

import json
from collections import defaultdict

import pandas as pd
import plotly.graph_objs as go

import dhis2
#import dhis_mets_or_ug

UG_OU_UID = 'akV6429SUqu'

_PCR_DE_UIDS = [
    ('I0MEbZSbEVs', 'Exposed Infants due for a test (1st PCR, 2nd PCR, 3rd PCR, & Rapid Test)'),
    ('y2G5UdgSfuk', '1st PCR'),
    ('XroPkgIGjVS', '2nd PCR'),
    ('tEYLrsgH6aO', '3rd PCR'),
    ('oX344XVLe1V', 'Rapid Test'),
    ('T2UepjeVadz', 'Positive Linked to ART'),
    ('o9Yy4ibSCWE', 'Positive'),
]

PCR_DE_UIDS = [ de_id for de_id, de_name in _PCR_DE_UIDS ]


def render_card_row(row_description, card_details):
    def render_card(card_name, card_content, card_description=''):
        return f'''
    <div class="card">
    <div class="card-block">

    <div class="card-title-block">
    <h3 class="title" style="white-space: nowrap"><span>{card_name}: </span></h3>
    </div>

    <section class="">
    <div class="">
    <h1 class="title"><span id="rr">{card_content}</span> <span id="ri"></span></h1>
    <p class="title-description" style="color: #7e8e9f">{card_description}</p>
    </div>
    </section>
    </div>
    </div>
    '''

    st.write(f'<h3 class="title">{row_description}</h3>', unsafe_allow_html=True)

    cols = st.beta_columns(len(card_details))

    for col, card_title in zip(cols, card_details):
        with col:
            card_html = render_card(card_title, *card_details[card_title])
            st.write(card_html, unsafe_allow_html=True)


@st.cache
def load_dhis2_data(server_url, credentials):
    instance = dhis2.Dhis2(server_url, credentials)
    dataelements = instance.dataelements()
    orgunits = instance.orgunits()

    return (instance, dataelements, orgunits)

st.set_page_config(layout='wide', page_title='Shema-Rwahi Demo')

query_params = st.experimental_get_query_params()
# st.write(query_params)

if 'u_passcode' not in st.session_state:
    st.session_state['u_passcode'] = ''

    if st.session_state['u_passcode'] != 'silverado':
        st.subheader('Privileged Access Required')
        pass_entry = st.text_input('Type Passcode:', type='password', key='u_passcode')
        if st.session_state['u_passcode'] == 'silverado':
            pass
        else:
            st.stop()

#with open('Coat_of_arms_of_Uganda.svg', 'r') as uganda_arms_file:
#    st.sidebar.image((''.join(l for l in uganda_arms_file))[113:], caption='Government of Uganda', width=48)
left_col, centre_col, right_col = st.beta_columns([1, 1, 1])

with left_col:
    st.image('Coat_of_arms_of_Uganda.png', caption='Government of Uganda', width=120)
with centre_col:
    st.title('MIS dashboard demo')

#mets_inst, dataelements, orgunits = load_dhis2_data(dhis_mets_or_ug.DHIS2_SERVER_URL, dhis_mets_or_ug.credentials)
mets_inst, dataelements, orgunits = load_dhis2_data(st.secrets['DHIS2_SERVER_URL'], tuple(st.secrets['credentials']))
#st.write([(de['id'], de['name']) for de in (dataelements[de_id] for de_id in PCR_DE_UIDS)])


df_mfl = pd.read_csv('UG_MFL_2021-04-21.csv')

df_districts = df_mfl[df_mfl['NAME'].isnull() & df_mfl['SUBCOUNTY'].isnull()].dropna(subset=['DISTRICT'])
REGIONS = [
    'Northern Region',
    'Eastern Region',
    'Central Region',
    'Western Region',
]
df_districts['region_index'] = df_districts['REGION'].map(lambda x: REGIONS.index(x) * 4)
#st.write(df_districts)

# st.write(f'Number of districts: {len(df_districts)}')

df_districts_unmappable = df_districts[df_districts['COORDINATES'] == '""']
df_districts_mappable = df_districts[df_districts['COORDINATES'] != '""']

# st.write('Unmappable districts:')
# st.write(df_districts_unmappable[['REGION', 'SUB_REGION', 'DISTRICT', 'COORDINATES']])

district_geojson = { 'type': 'FeatureCollection', 'features': list() }
mappable_district_uids = list()

for row in df_districts.itertuples():
    d = {
    'type': 'Feature',
    'geometry': json.loads(row.COORDINATES),
    'properties': { 'name': row.DISTRICT, 'region': row.REGION, 'subregion': row.SUB_REGION, 'uid': row.UID },
    'id': row.DISTRICT,
    }
    district_geojson['features'].append(d)
    if row.UID not in ['bJgx6UjvyoP']:
        mappable_district_uids.append(row.UID)

# st.write(district_geojson['features'][:2])

left_col, right_col = st.beta_columns([1, 1])
with right_col:
    st.write("<b>1 - Production, Processing, Value Addition and Marketing</b>", unsafe_allow_html=True)
    st.write("<b>2 - Infrastructure and Economic Services</b>", unsafe_allow_html=True)
    st.write("<b>3 - Financial Inclusion</b>", unsafe_allow_html=True)
    st.write("<b>4 - Health</b>", unsafe_allow_html=True)
    st.write("<b>5 - Education</b>", unsafe_allow_html=True)
    st.write("<b>6 - Social Services Delivery</b>", unsafe_allow_html=True)
    st.write("<b>7 - Community Information</b>", unsafe_allow_html=True)
    st.write("<b>8 - Governance and Administration</b>", unsafe_allow_html=True)
    st.write("<b>9 - Mindset Change</b>", unsafe_allow_html=True)

fig = go.Figure(go.Choroplethmapbox(geojson=district_geojson, locations=df_districts_mappable.DISTRICT, z=df_districts_mappable.region_index, colorscale='Cividis',zmin=0,zmax=17, marker_opacity=0.5, marker_line_width=0))
fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=5.5, mapbox_center = {"lat": 0.6226, "lon": 32.3271})
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
left_col.write(fig)



district_tuples = [tuple(x) for _, *x in df_districts.filter(items=['DISTRICT', 'UID']).itertuples()]

MISSING_DISTRICTS = ('Kassanda District', 'Obongi District', 'Terego District') # eHMIS districts that are not in OptionB
MISMATCH_DISTRICTS = [(x_name, x_uid) for x_name, x_uid in district_tuples if x_uid not in orgunits]
# for x_name, x_uid in MISMATCH_DISTRICTS:
#     #st.write((x_name, x_uid))
#     if x_name not in MISSING_DISTRICTS:
#         x_ou = orgunits.lookup_name(x_name)
#         st.write((x_name, x_uid, x_ou['id']))

left_col, center_col, right_col = st.beta_columns([1, 1, 1])
with left_col:
    district_selected = st.selectbox('Select a district:', options=[('<No District>', UG_OU_UID),*district_tuples], format_func=lambda x: x[0])

district_name, district_uid = district_selected
if district_uid != UG_OU_UID:
    # st.write('Chosen District is ', district_selected)
    pass
else:
    district_name = 'Uganda'
    # st.write(f'No Chosen District (defaulting to National {district_name})')

#TODO: national eHMIS and OptionB don't agree on Kampala District (and others??)
TT_1 = [
    ('Amudat District', 'a8RHFdF4DXL', 'h8RHFdF4DXL'),
    ('Bugweri District', 'AIonX4LaJeU', 'JzUtuySAs8W'),
    ('Bunyangabu District', 'iTfbtn6JUsN', 'uAUn3ZcQ6Kt'),
    ('Butebo District', 'FDPqRvcW3NN', 'y2TckWz9CPy'),
    ('Buvuma District', 'aZLZPPjqft0', 'bZLZPPjqft0'),
    ('Jinja District', 'aJR2ZxSH7g4', 'gJR2ZxSH7g4'),
    ('Kabarole District', 'm77oR1YJESj', 'fIbu0dVl0gz'),
    ('Kagadi District', 'orgY0d5MJa9', 'LtyM5HnzFui'),
    ('Kakumiro District', 'Lnewt3iIJaK', 'HRakdY52JPf'),
    ('Kalaki District', 'KOnkIf4N6jA', 'TCtwiCWcvMh'),
    ('Kampala District', 'aXmBzv61LbM', 'rzsbhKKYISq'),
    ('Kamwenge District', 'uCVQXAdKqL9', 'VbX669lGEiY'),
    ('Kanungu District', 'aphcy5JTnd6', 'ophcy5JTnd6'),
    ('Kapchorwa District', 'aginheWSLef', 'iginheWSLef'),
    ('Kapelebyong District', 'mvN9LBbpf7X', 'OK3JLtXYKzL'),
    ('Karenga District', 'Hmh5JQLls1d', 'XrzjPNEakFG'),
    ('Kasese District', 'aa8xVDzSpte', 'fa8xVDzSpte'),
    ('Kazo District', 'AS2Seq1grGE', 'BJ9capKA8Kg'),
    ('Kibaale District', 'tM3DsJxMaMX', 'AtnLKczpkvP'),
    ('Kikuube District', 'L5WBetpBpY3', 'fXT6ayIyYeH'),
    ('Kisoro District', 'aPhSZRinfbg', 'dPhSZRinfbg'),
    ('Kitagwenda District', 'qKmESX5Owwr', 'ROQiyOthHFm'),
    ('Kwania District', 'gCN6sU5BjlR', 'es2NjGbxNBy'),
    ('Kyegegwa District', 'a9tQqo1rSj7', 'g9tQqo1rSj7'),
    ('Kyotera District', 'REJuxCmTwXG', 'UcOzqLVFJVo'),
    ('Lwengo District', 'aqpd0Y9eXZ2', 'bqpd0Y9eXZ2'),
    ('Lyantonde District', 'aPRNSGUR3vk', 'ePRNSGUR3vk'),
    ('Madi-Okollo District', 'bLoH4VbxCGI', 'eqfJd1Yk9u4'),
    ('Mbarara District', 'auswb7JO9wY', 'huswb7JO9wY'),
    ('Mpigi District', 'YMMexeHFUay', 'bFlqjkzbC8N'),
    ('Mukono District', 'a0DfYpC2Rwl', 'd0DfYpC2Rwl'),
    ('Nabilatuk District', 'mOXva2xiwQv', 'Ma6LKsXVlDm'),
    ('Nakaseke District', 'aSbgVKaeCP0', 'oSbgVKaeCP0'),
    ('Nakasongola District', 'aUcYGQCK9ub', 'hUcYGQCK9ub'),
    ('Namisindwa District', 'TGzZPOmbgn8', 's3X2onnu3iE'),
    ('Ngora District', 'aj4hsYK3dVm', 'hj4hsYK3dVm'),
    ('Omoro District', 'S5fvUXgY54J', 'yIWARgfOvr1'),
    ('Otuke District', 'aXjub1BYn1y', 'dXjub1BYn1y'),
    ('Pader District', 'aBrjuZk0W31', 'gBrjuZk0W31'),
    ('Pakwach District', 'uqUyTPvQKII', 'StgiDC6czID'),
    ('Rubanda District', 'wZrfAgC3WrU', 'N9zP0kGK7Ld'),
    ('Rukiga District', 'fsP0Wxie1UW', 'mb3idsHFRl6'),
    ('Rwampara District', 'tsugXWRXwGu', 'WDgr6qVSjB6'),
]
EHMIS_OPTIONB_MAP = { ehmis_uid:optionb_uid for _, ehmis_uid, optionb_uid in TT_1 }
if district_uid in EHMIS_OPTIONB_MAP:
    district_uid = EHMIS_OPTIONB_MAP[district_uid]
#if district_uid == 'aXmBzv61LbM': # Kampala
#    district_uid = 'rzsbhKKYISq'
#if district_uid == 'Gwk4wkLz7EW': # Gulu
#    district_uid = 'tEYLrsgH6aO'

UBOS_PARISH_PATH = 'ubos_parish'
parish_path = 'ubos_parish/ALL_POP.csv'

df_parish = pd.read_csv(parish_path)
#st.write(df_parish)

if district_name != 'Uganda':
    df_district_parishes = df_parish[df_parish['District'] == district_name.replace(' District', '')]
    # st.write(df_district_parishes)
    
    with center_col:
        subcounty_arr = df_district_parishes['Subcounty'].unique()
        # st.write(subcounty_arr)
        subcounty_tuples = [(x,x) for x in subcounty_arr]
        subcounty_selected = st.selectbox('Select subcounty:', options=['<No Subcounty>', *subcounty_arr])
        if subcounty_selected != '<No Subcounty>':
            subcounty_name = str(subcounty_selected)
        else:
            subcounty_name = None

    if subcounty_name:
        with right_col:
            parish_arr = df_district_parishes[df_district_parishes['Subcounty'] == subcounty_name]['Parish'].unique()
            # st.write(parish_arr)
            parish_tuples = [(x,x) for x in parish_arr]
            parish_selected = st.selectbox('Select parish:', options=['<No parish>', *parish_arr])
            if parish_selected != '<No parish>':
                parish_name = str(parish_selected)
            else:
                parish_name = None
    
    df_subcounty_pop = df_district_parishes[['District', 'County', 'Subcounty', 'Parish', 'Pop_Total']].groupby(['District', 'County', 'Subcounty']).sum()
    # st.write(df_subcounty_pop)

    # for row in df_subcounty_pop.itertuples():
    #     st.write(row)

    # st.write({ row[0][-1]: [row[1],] for row in df_subcounty_pop.itertuples() })
    tt = df_district_parishes[['Subcounty', 'Parish', 'Pop_Total']].groupby(['Subcounty',]).agg(parish_list=('Parish', lambda x: ', '.join(x)), subcounty_pop=('Pop_Total', sum))
    # st.write(tt)
    # st.write({ row[0]: [row[2], row[1]] for row in tt.itertuples() })
    # render_card_row(f'Population Statistics [{len(df_subcounty_pop)} subcounties, {len(df_district_parishes)} parishes]', { row[0]: [row[2], row[1]] for row in tt.itertuples() })
else:
    subcounty_name = None
    parish_name = None

# df_optionb_all = pd.read_csv('optionb_plus.csv')
df_optionb_all = pd.read_csv('optionb_plus2.csv')
df_optionb = df_optionb_all[df_optionb_all['Organisation unit'] == district_uid]
df_optionb['shortName'] = df_optionb['Data'].map(lambda x: dataelements[x]['name'][6:].replace('Tested ', '', 1).replace('Total Number ', '', 1))
# st.write(df_optionb) # DEBUG: OptionB+ cascade for selected district

xx = { a: (d, c) for _, a, b, c, d in df_optionb.itertuples() }

pcr_cascade = [xx.get(uid) for uid in PCR_DE_UIDS[:5]] # first 5 form the cascade
linkage_cascade = [xx.get(uid) for uid in PCR_DE_UIDS[5:]] # last 2 form the linkage
if (not all(pcr_cascade) or not all(linkage_cascade)): # TODO: very conservative check!
    pmtct_title = f'HIV Mother-to-Child: 2021W16 ({district_name})'
    pmtct = {
        'Reporting Rate': [ 'N/A', 'No data available' ],
        'Babies tested': [ 'N/A', 'No data available' ],
        'HIV+ infants linked to care': [ 'N/A', 'No data available' ],
    }
else:
    (_, pcr_eid), *pcr_cascade = pcr_cascade
    pcr_cascade_text = ', '.join([f'<span><a>{int(val)}</a></span> :{name}' for name, val in pcr_cascade])
    pcr_rate = sum((v for _, v in pcr_cascade)) / int(pcr_eid)

    linkage_cascade_text = ', of '.join([f'<span><a>{int(val)}</a></span> {name}' for name, val in linkage_cascade])
    if linkage_cascade[1][1] == 0:
        linkage_rate = 1
        linkage_cascade_text = 'Zero HIV+ cases found in Exposed Infants'
    else:
        linkage_rate = linkage_cascade[0][1] / linkage_cascade[1][1]

    #st.write(pcr_cascade, pcr_rate)
    #st.write(pcr_cascade_text, unsafe_allow_html=True)
    #st.write(linkage_cascade, linkage_rate)
    #st.write(linkage_cascade_text, unsafe_allow_html=True)

    pmtct_title = f'HIV Mother-to-Child: 2021W16 ({district_name})'
    pmtct = {
        'Reporting Rate': [ '19%', '<a href="#">317</a> of <a href="#">1648</a> reports received' ],
        'Babies tested': [ f'{pcr_rate:.1%}', f'({pcr_cascade_text}) of {int(pcr_eid)} Exposed Infants' ],
        'HIV+ infants linked to care': [ f'{linkage_rate:.1%}', linkage_cascade_text ],
    }


# render_card_row(pmtct_title, pmtct)

if district_name and subcounty_name and parish_name:
    # st.write(df_subcounty_pop)
    tt = df_district_parishes[(df_district_parishes['District'] == district_name.replace(' District', '')) & (df_district_parishes['Subcounty'] == subcounty_name) & (df_district_parishes['Parish'] == parish_name)]
    parish_pop = tt['Pop_Total'].values[0]
    # st.write(tt)
    st.header(f"{parish_name} Parish [Population: {parish_pop}] - {subcounty_name}, {district_name}")
    # st.header("Katooma Parish [Population: 5589] - Rwahi Town Council, Ntungamo District")

    with st.beta_expander("Production, Processing, Value Addition and Marketing"):
        st.write("""
<ol>
    <li><h3>Production</h3>
        <ul>
        <li>Crops Grown for Commercial purposes
            <ul>
                <li>
                <div>Onions</div>
                <p>
                Number of registered growers: 411<br/>
                Number of registered grower associations: 17<br/>
                Number of approved storage facilities: 2<br/>
                Quantity (tonnes) sold: 1754.5<br/>
                Farm gate price (UGX/tonnes): 70000<br/>
                </p>
                </li>
                <li>Sweet Potatoes</li>
                <li>Cabbages</li>
            </ul>
        </li>
        </ul>
    </li>
    <li><h3>Processing</h3>
        <ul>
        <li>Processed Agricultural Produce
            <ul>
                <li>
                <div>Onions (Sun-dried)</div>
                Quantity (tonnes): 600</br>
                </li>
                <li>
                <div>Onion slices (package)</div>
                Quantity (tonnes): 97</br>
                </li>
            </ul>
        <li>
        </ul>
    </li>
    <li><h3>Value Addition</h3>
        <ul>
        <li>Value Added Agricultural Produce
            <ul>
                <li>
                <div>Onion Powder</div>
                Quantity (tonnes): 230</br>
                Value-adding groups/entities: Rwahi Spice Cooperative</br>
                </li>
            </ul>
        </li>
        </ul>
    </li>
    <li><h3>Marketing</h3>
        <ul>
        <li>Marketing Association
            <ul>
                <li>
                <div>Onions</div>
                Farmers Cooperative: Banyankole Kweterana</br>
                </li>
            </ul>
        </li>
        </ul>
    </li>
</ol>
"""
        , unsafe_allow_html=True)
    with st.beta_expander("Infrastructure and Economic Services"):
        st.write("""
<ol>
    <li><h3>Electricity</h3>
        <ul>
        <li>Electricity Coverage
            <ul>
                <li>
                <p>
                Number of households connected to grid power: 411<br/>
                Number of households using solar: 17<br/>
                Number of using traditional lighting (tadooba etc): 2<br/>
                </p>
                </li>
            </ul>
        </li>
        </ul>
    </li>
    <li><h3>Roads</h3>
        <ul>
        <li>Road Coverage
            <ul>
                <li>
                Tarmac Road (kms): 12</br>
                Murram Road (kms): 10</br>
                Impassable Road (kms): 8</br>
                </li>
            </ul>
        </li>
        <li>Bridges
            <ul>
                <li>
                Existing: 1</br>
                Needed: 1</br>
                </li>
            </ul>
        </li>
        </ul>
    </li>
    <li><h3>Markets</h3>
        <ul>
        <li>Electricity Coverage
            <ul>
                <li>
                <p>
                Weekly Markets: 2<br/>
                Permanent Markets: 1<br/>
                </p>
                </li>
            </ul>
        </li>
        </ul>
    </li>
</ol>
"""
        , unsafe_allow_html=True)
    with st.beta_expander("Financial Inclusion"):
        st.write("""
<ol>
    <li><h3>Banks and Savings Societies</h3>
        <ul>
        <li>Electricity Coverage
            <ul>
                <li>
                <p>
                Number of households connected to grid power: 411<br/>
                Number of households using solar: 17<br/>
                Number of using traditional lighting (tadooba etc): 2<br/>
                </p>
                </li>
            </ul>
        </li>
        </ul>
    </li>
    <li><h3>Access to Credit</h3>
        <ul>
        <li>SACCOs and Cooperatives
            <ul>
                <li>
                <p>
                Number of savings organisations: 411<br/>
                Number of savers/participants: 411<br/>
                </p>
                </li>
            </ul>
        </li>
        <li>Grants, Youth Development funds
            <ul>
                <li><div>Youth Development Loans/Grants</div>
                <p>
                Number of youth associations that have received loans: 17<br/>
                Number of youth associations that have received loans: 17<br/>
                </p>
                </li>
                <li><div>Emyooga<div>
                <p>
                Number of beneficiary associations: 411<br/>
                Number of members of beneficiary associations: 17<br/>
                </p>
                </li>
                <li><div>Byona Bagagawale<div>
                <p>
                Number of beneficiary associations: 411<br/>
                Number of members of beneficiary associations: 17<br/>
                </p>
                </li>
            </ul>
        </li>
        </ul>
    </li>
</ol>
"""
        , unsafe_allow_html=True)
    with st.beta_expander("Health"):
        pass
    with st.beta_expander("Education"):
        pass
    with st.beta_expander("Social Service Delivery"):
        st.write("""
<ol>
    <li><h3>Water and Sanitation</h3>
        <ul>
        <li>Water Sources
            <ul>
                <li>
                <p>
                Piped and Tap: 411<br/>
                Boreholes: 411<br/>
                Wells: 411<br/>
                Open Waterbodies (lakes, rivers, streams): <br/>
                </p>
                </li>
            </ul>
        </li>
        <li>Hygiene
            <ul>
                <li><div>Access to Toilet facilities</div>
                <p>
                Modern Latrine: 17<br/>
                Other toilet facility: 17<br/>
                </p>
                </li>
                <li><div>Manner of Waste Disposal<div>
                <p>
                Percentage of households that properly dispose of solid waste: 17<br/>
                </p>
                </li>
            </ul>
        </li>
        </ul>
    </li>
    <li><h3>Social Development Services</h3>
    </li>
</ol>
"""
        , unsafe_allow_html=True)
    with st.beta_expander("Community Information"):
        pass
    with st.beta_expander("Governance and Administration"):
        st.write("""
<ol>
    <li><h3>Local Government</h3>
        <ul>
        <li>Local Leadership
            <ul>
                <li>
                <p>
                Number of local council officials: 6<br/>
                &lt;Name&gt; &lt;Designation&gt;<br/>
                &lt;Name&gt; &lt;Designation&gt;<br/>
                &lt;Name&gt; &lt;Designation&gt;<br/>
                &lt;Name&gt; &lt;Designation&gt;<br/>
                &lt;Name&gt; &lt;Designation&gt;<br/>
                &lt;Name&gt; &lt;Designation&gt;<br/>
                </p>
                </li>
            </ul>
        </li>
        </ul>
    </li>
</ol>
"""
        , unsafe_allow_html=True)
    with st.beta_expander("Mindset Change"):
        pass
