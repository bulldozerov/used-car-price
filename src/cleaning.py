

df_clean = df_merged.copy()
df_clean['listing_id'] = df_clean['link'].str.extract(r'/show/(\d+)')[0]



BODY_DICT = {
    'седан': 'sedan', 'кроссовер': 'crossover', 'хэтчбек': 'hatchback',
    'универсал': 'wagon', 'лифтбек': 'liftback', 'внедорожник': 'suv',
    'минивэн': 'minivan', 'микровэн': 'minivan', 'микроавтобус': 'minibus',
    'купе': 'coupe', 'пикап': 'pickup', 'кабриолет': 'convertible',
    'фургон': 'van', 'лимузин': 'limousine', 'хардтоп': 'hardtop'
}
FUEL_DICT = {
    'бензин': 'petrol', 'дизель': 'diesel', 'газ': 'lpg',
    'газ-бензин': 'lpg+petrol', 'гибрид': 'hybrid', 'электричество': 'electric'
}
KPP_DICT = {
    'механика': 'manual', 'автомат': 'automatic',
    'вариатор': 'cvt', 'робот': 'robot'
}



def parse_car_desc(desc):
    r = dict(on_order=False, year_d=np.nan, cond_d=None, body=None, engine_d=np.nan,
             fuel_d=None, trans_d=None, mileage_d=np.nan, right_hand=False, metallic=False)
    if not isinstance(desc, str):
        return r
    for s in (x.strip() for x in desc.split(',')):
        low = s.lower()
        if low == 'на заказ':
            r['on_order'] = True; continue
        if re.fullmatch(r'(19|20)\d{2}\s*г\.?', s):
            r['year_d'] = int(s[:4]); continue
        m = re.fullmatch(r'(новый|б/у)\s+([а-яё]+)', low)
        if m:
            r['cond_d'] = 'new' if m.group(1) == 'новый' else 'used'
            r['body'] = BODY_DICT.get(m.group(2)); continue
        m = re.fullmatch(r'(\d+(?:[.,]\d+)?)\s*л', low)
        if m:
            r['engine_d'] = float(m.group(1).replace(',', '.')); continue
        if low in FUEL_DICT:
            r['fuel_d'] = FUEL_DICT[low]; continue
        m = re.fullmatch(r'кпп\s+([а-яё]+)', low)
        if m:
            r['trans_d'] = KPP_DICT.get(m.group(1)); continue
        m = re.fullmatch(r'(\d+(?:[.,]\d+)?)\s*тыс\.?\s*км', low)
        if m:
            r['mileage_d'] = float(m.group(1).replace(',', '.')) * 1000; continue
        m = re.fullmatch(r'(?:с пробегом\s+)?(\d[\d\s\u00a0]*)\s*км', low)
        if m:
            r['mileage_d'] = float(re.sub(r'\D', '', m.group(1))); continue
        if low == 'правый руль':
            r['right_hand'] = True
        if low.startswith('металлик'):
            r['metallic'] = True
    return r

def add_parsed_columns(df, desc_col='desc'):
    parsed = pd.DataFrame(df[desc_col].map(parse_car_desc).tolist(), index=df.index)
    return pd.concat([df, parsed], axis=1)


def check_agreement(col_site, col_parsed):
    mask = col_site.notna() & col_parsed.notna()

    return pd.Series({
        'Compared rows': int(mask.sum()),
        'Match, %': round(100.0 * (col_site[mask] == col_parsed[mask]).mean(), 2)
    })

def build_validation_table(df):
    return pd.DataFrame({
        'Year (year)': check_agreement(df.year, df.year_d),
        'Condition (condition)': check_agreement(df.condition, df.cond_d),
        'Transmission (transmission)': check_agreement(df.transmission, df.trans_d),
        'Engine volume (engine_l)': check_agreement(df.engine_liters, df.engine_d),
        'Mileage (mileage_km)': check_agreement(df.mileage_km, df.mileage_d),
    }).T