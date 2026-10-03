from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import parse_qs,urlparse
import hashlib,html,os,secrets,sqlite3,json

ROOT=os.path.dirname(os.path.abspath(__file__)); DB=os.path.join(ROOT,'flowers.sqlite3'); STATIC=os.path.join(ROOT,'static'); SESSIONS={}
SEED=[('Пионовый вечер','Букеты','Пионы, розы и эвкалипт в спокойной палитре.',4590,'/static/images/bouquet1.jpg'),('Нежное утро','Букеты','Розовые розы и кремовая гортензия.',3290,'/static/images/bouquet2.jpg'),('Садовая история','Композиции','Свежая композиция с сезонной зеленью.',5190,'/static/images/bouquet3.jpg'),('Белая классика','Розы','Лаконичный букет из белых роз.',3890,'/static/images/bouquet4.jpg'),('Тёплое письмо','Подарки','Букет с открыткой для важного человека.',2790,'/static/images/bouquet5.jpg'),('Ваза с ранункулюсами','Композиции','Небольшая интерьерная композиция.',3490,'/static/images/bouquet6.jpg')]
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def pwd(v): return hashlib.sha256(v.encode()).hexdigest()
def init_db():
    c=db(); c.executescript(open(os.path.join(ROOT,'schema.sql'),encoding='utf-8').read())
    if c.execute('SELECT COUNT(*) FROM products').fetchone()[0]==0:c.executemany('INSERT INTO products(name,category,description,price,image_url) VALUES(?,?,?,?,?)',SEED)
    if not c.execute("SELECT 1 FROM users WHERE email='admin@flowers.local'").fetchone():c.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)',('Администратор','admin@flowers.local',pwd('admin123'),'admin'))
    c.commit(); c.close()
def esc(v): return html.escape(str(v or ''))
def user(h):
    raw=h.headers.get('Cookie','')
    for part in raw.split(';'):
        if part.strip().startswith('sid='): return SESSIONS.get(part.strip().split('=',1)[1])
    return None
def shell(title,body,u):
    nav='<a href="/">ГЛАВНАЯ</a><a href="/?page=catalog">КАТАЛОГ</a><a href="/?page=builder">СОБРАТЬ БУКЕТ</a><a href="/?page=delivery">ДОСТАВКА</a><a href="/?page=reviews">ОТЗЫВЫ</a><a href="/?page=contacts">КОНТАКТЫ</a>'
    acc='<a class="button small auth-button" style="color:#fff!important" href="/?page=admin">Админ-панель</a>' if u and u['role']=='admin' else ('<a class="button small auth-button" style="color:#fff!important" href="/?page=account">Кабинет</a>' if u else '<a class="button small auth-button" style="color:#fff!important" href="/?page=login">Войти</a>')
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} — Цветочный Рай</title><link rel="stylesheet" href="/static/style.css"></head><body><header><a class="brand" href="/"><span class="brand-mark">♧</span><span>Цветочный Рай<small>Цветы, которые говорят за вас</small></span></a><nav>{nav}</nav><div class="actions"><a class="heart" href="/?page=cart">♡</a><a class="cart" href="/?page=cart">♧ <b id="cart-count">0</b></a>{acc}</div></header><main>{body}</main><footer><a class="brand" href="/"><span class="brand-mark">♧</span><span>Цветочный Рай<small>Цветы, которые говорят за вас</small></span></a><div><h3>Навигация</h3><a href="/?page=catalog">Каталог</a><a href="/?page=builder">Собрать букет</a><a href="/?page=delivery">Доставка</a><a href="/?page=reviews">Отзывы</a></div><div><h3>Информация</h3><a href="/?page=contacts">Контакты</a><a href="/?page=contacts">О нас</a><a href="/?page=contacts">Политика конфиденциальности</a></div><div><h3>Контакты</h3><p>+7 (999) 123-45-67</p><p>info@flowerparadise.ru</p><p>г. Москва, ул. Цветочная, 12</p></div><p class="copyright">© 2026 Цветочный Рай. Все права защищены.</p></footer><script src="/static/app.js"></script></body></html>'''
def cards(rows):
    return ''.join(f'''<article class="card"><div class="card-image"><img src="{esc(r['image_url'])}" alt="{esc(r['name'])}"><button class="fav">♡</button></div><div class="card-body"><h3>{esc(r['name'])}</h3><div class="card-bottom"><strong>{r['price']:.0f} ₽</strong><button class="add-to-cart add" data-id="{r['id']}" data-name="{esc(r['name'])}" data-price="{r['price']}">В корзину <span>♧</span></button></div></div></article>''' for r in rows)
def home(c):
    return '''<section class="hero"><div class="hero-copy"><h1>Цветочный Рай</h1><p class="lead">Цветы, которые говорят за вас</p><div class="hero-actions"><a class="button" href="/?page=catalog">Смотреть каталог</a><a class="button outline" href="/?page=builder">Собрать букет</a></div></div><div class="hero-art"><img src="/static/images/bouquet1.jpg" alt="Букет цветов"></div></section><section class="section-block"><div class="section-heading"><div><p class="eyebrow">НАШИ БУКЕТЫ</p><h2>Популярные букеты</h2></div><a class="text-link" href="/?page=catalog">Смотреть все →</a></div><section class="grid">'''+cards(c.execute('SELECT * FROM products WHERE is_active=1 LIMIT 4').fetchall())+'''</section></section><section class="season"><p class="eyebrow">ПРИРОДА В ДЕТАЛЯХ</p><h2>Сезонные цветы</h2><div class="tabs"><span class="active">Весна</span><span>Лето</span><span>Осень</span><span>Зима</span></div><section class="grid seasonal-grid">'''+cards(c.execute('SELECT * FROM products WHERE is_active=1 LIMIT 4 OFFSET 2').fetchall())+'''</section></section><section class="why"><p class="eyebrow">ПОЧЕМУ МЫ?</p><h2>Делаем с любовью</h2><div class="why-grid"><div><b>✿</b><h3>Свежесть</h3><p>Только свежие цветы от проверенных поставщиков</p></div><div><b>♧</b><h3>Быстрая доставка</h3><p>Доставим букет в день заказа</p></div><div><b>♡</b><h3>Ручная сборка</h3><p>Каждый букет собирается вручную</p></div></div></section><section class="reminder"><h2>Скоро чей-то день рождения?</h2><p>Порадуйте близких красивым букетом</p><a class="button" href="/?page=catalog">Выбрать подарок</a></section>'''
def catalog(c): return '<section class="page-head catalog-head"><h1>Каталог букетов</h1><p>Более 100 уникальных композиций для любого случая</p><input class="search" placeholder="⌕  Поиск по названию..."></section><div class="catalog-layout"><aside class="filters"><h2>Фильтры</h2><h3>По поводу</h3>'+''.join(f'<span class="chip {"active" if x=="Все" else ""}">{x}</span>' for x in ["Все","День рождения","Свадьба","Романтика","Юбилей","Соболезнования"])+'<h3>Сезон</h3>'+''.join(f'<span class="chip">{x}</span>' for x in ["Все","Весна","Лето","Осень","Зима"])+'<h3>Цена</h3><input type="range" min="0" max="10000" value="10000"></aside><div class="catalog-results"><div class="result-bar">Найдено: <b>12</b> букетов <select><option>Популярные</option><option>Новинки</option><option>Цена: по возрастанию</option></select></div><section class="grid">'+cards(c.execute('SELECT * FROM products WHERE is_active=1 ORDER BY id LIMIT 6').fetchall())+'</section></div></div>'
def auth(kind):
    reg=kind=='register'; title='Создать аккаунт' if reg else 'С возвращением'; fields='<input name="name" placeholder="Ваше имя" required>' if reg else ''
    hint='Уже есть аккаунт? <a href="/?page=login">Войти</a>' if reg else 'Нет аккаунта? <a href="/?page=register">Зарегистрироваться</a>'
    return f'<section class="auth"><div><p class="eyebrow">FLOWERS STUDIO</p><h1>{title}</h1><p class="lead">Войдите, чтобы отслеживать заказы и сохранять любимые букеты.</p></div><form class="form" method="post" action="/?action={kind}">{fields}<input type="email" name="email" placeholder="Email" required><input type="password" name="password" placeholder="Пароль" minlength="6" required><button class="button" type="submit">{title} <span>↗</span></button><p class="form-note">{hint}</p></form></section>'
def account(c,u):
    rows=c.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC',(u['id'],)).fetchall(); tr=''.join(f'<tr><td>#{r["id"]}</td><td>{esc(r["delivery_date"])}</td><td>{r["total"]:.0f} ₽</td><td><span class="status">{esc(r["status"])}</span></td></tr>' for r in rows) or '<tr><td colspan="4">Заказов пока нет</td></tr>'
    return f'<section class="page-head"><p class="eyebrow">ЛИЧНЫЙ КАБИНЕТ</p><h1>Здравствуйте, {esc(u["name"])}!</h1><p>{esc(u["email"])} · <a href="/?action=logout">Выйти</a></p></section><section class="panel"><h2>Мои заказы</h2><table><thead><tr><th>Номер</th><th>Дата доставки</th><th>Сумма</th><th>Статус</th></tr></thead><tbody>{tr}</tbody></table></section>'
def builder(): return '<section class="builder"><div><p class="eyebrow">КОНСТРУКТОР</p><h1>Соберите букет<br><em>по своему вкусу</em></h1><p class="lead">Выберите настроение и добавьте открытку. Флорист соберёт композицию вручную.</p><form class="form" onsubmit="event.preventDefault();alert(\'Заявка отправлена\')"><label>Повод<select><option>День рождения</option><option>Свидание</option><option>Просто так</option></select></label><label>Палитра<select><option>Нежная</option><option>Яркая</option><option>Белая</option></select></label><textarea placeholder="Пожелания флористу"></textarea><button class="button">Продолжить <span>↗</span></button></form></div><img src="/static/images/bouquet5.jpg" alt="Конструктор букета"></section>'
def info_page(kind):
    if kind=='delivery': return '''<section class="page-head"><p class="eyebrow">ЦВЕТОЧНЫЙ РАЙ</p><h1>Доставка</h1><p>Бережно доставим ваш букет в нужное время</p></section><section class="info-grid"><div class="panel"><h2>Курьерская доставка</h2><p>Доставляем по Москве ежедневно с 9:00 до 21:00. Выберите удобную дату и интервал при оформлении.</p></div><div class="panel"><h2>Стоимость</h2><p>По Москве — от 350 ₽. Точная стоимость рассчитывается по адресу. Срочная доставка доступна по согласованию.</p></div><div class="panel"><h2>Как получить заказ</h2><p>Курьер позвонит за 30 минут до приезда. Букет будет упакован в защитную коробку и сохранит свежесть.</p></div></section>'''
    if kind=='reviews': return '''<section class="page-head"><p class="eyebrow">ЦВЕТОЧНЫЙ РАЙ</p><h1>Отзывы</h1><p>Нам доверяют важные моменты</p></section><section class="review-grid"><div class="panel"><h2>«Очень красиво!»</h2><p>Букет приехал свежим, аккуратно собранным и точно соответствовал фотографии.</p><strong>— Анна, Москва</strong></div><div class="panel"><h2>«Всё получилось»</h2><p>Спасибо флористу за точное попадание в палитру. Доставка приехала вовремя.</p><strong>— Максим, Москва</strong></div><div class="panel"><h2>«Буду заказывать ещё»</h2><p>Понравился сайт, выбор цветов и заботливое отношение к заказу.</p><strong>— Елена, Химки</strong></div></section>'''
    if kind=='contacts': return '''<section class="page-head"><p class="eyebrow">ЦВЕТОЧНЫЙ РАЙ</p><h1>Контакты</h1><p>Мы всегда на связи</p></section><section class="contact-grid"><div class="panel"><h2>Свяжитесь с нами</h2><p>Телефон: <a href="tel:+79991234567">+7 (999) 123-45-67</a></p><p>Email: <a href="mailto:info@flowerparadise.ru">info@flowerparadise.ru</a></p><p>Ежедневно с 9:00 до 21:00</p></div><div class="panel"><h2>Наш адрес</h2><p>г. Москва, ул. Цветочная, 12</p><p>Вход со стороны цветочного переулка.</p><a class="button" href="https://maps.google.com/?q=Москва+ул.+Цветочная+12">Построить маршрут</a></div></section>'''
    if kind=='cart': return '''<style>.cart-row{display:flex;align-items:center;gap:24px;padding:18px 0;border-bottom:1px solid #e2d9d0}.cart-row>div:first-child{flex:1}.cart-row h2{font-size:19px}.cart-row p{color:#a6b09d}.qty{display:flex;align-items:center;gap:12px}.qty button,.remove{border:1px solid #d8cec4;background:#fff;border-radius:18px;padding:7px 12px;color:#536449}.remove{background:#f7e9df}.cart-total{display:flex;justify-content:flex-end;align-items:center;gap:16px;margin-top:20px}.cart-total h2{margin-right:auto;font-family:'Playfair Display',serif}.info-grid,.review-grid,.contact-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:1050px;margin:auto}.contact-grid{grid-template-columns:1fr 1fr}.info-grid p,.review-grid p,.contact-grid p{color:#899584;line-height:1.7}@media(max-width:700px){.info-grid,.review-grid,.contact-grid{grid-template-columns:1fr}.cart-row{flex-wrap:wrap}.cart-total{flex-wrap:wrap}.cart-total h2{width:100%}}</style><section class="page-head"><p class="eyebrow">ЦВЕТОЧНЫЙ РАЙ</p><h1>Корзина</h1><p>Проверьте состав заказа перед оформлением</p></section><section id="cart-root" class="cart-root"></section>'''
    return '<section class="empty"><h1>Flowers Studio</h1></section>'
CRUD_TABLES=['users','products','orders','order_items','reviews']
def crud_form(c,table,edit=None):
    cols=[x for x in c.execute(f'PRAGMA table_info({table})') if x[5]==0 and x[1] not in ('created_at',)]
    vals=dict(c.execute(f'SELECT * FROM {table} WHERE id=?',(edit,)).fetchone() or {})
    fields=''.join(f'<input name="{x[1]}" placeholder="{x[1]}" value="{esc(vals.get(x[1],""))}" required>' for x in cols if x[1]!='id')
    return f'<section class="auth"><div><p class="eyebrow">CRUD</p><h1>{"Изменить" if edit else "Добавить"} запись</h1><p>Таблица {table}</p></div><form class="form" method="post" action="/?action=crud"><input type="hidden" name="table" value="{table}"><input type="hidden" name="id" value="{edit or ""}"><input type="hidden" name="crud" value="{"update" if edit else "add"}">{fields}<button class="button">Сохранить <span>↗</span></button></form></section>'
def admin(c):
    out='<section class="page-head"><p class="eyebrow">FLOWERS STUDIO</p><h1>Административная панель</h1><p>Таблицы базы данных и представления.</p></section>'; tables=['users','products','orders','order_items','reviews']
    for n in tables:
        rows=c.execute(f'SELECT * FROM {n} LIMIT 30').fetchall(); cols=list(rows[0].keys()) if rows else [x[1] for x in c.execute(f'PRAGMA table_info({n})')]; th=''.join(f'<th>{x}</th>' for x in cols)+'<th>Операции</th>'; tr=''.join('<tr>'+''.join(f'<td>{esc(r[x])}</td>' for x in cols)+f'<td><a href="/?page=crud&table={n}&edit={r["id"]}">Изменить</a> <form method="post" action="/?action=crud" style="display:inline"><input type="hidden" name="crud" value="delete"><input type="hidden" name="table" value="{n}"><input type="hidden" name="id" value="{r["id"]}"><button type="submit">Удалить</button></form></td></tr>' for r in rows); out+=f'<section class="panel"><div class="panel-title"><h2>{n}</h2><a class="button small" href="/?page=crud&table={n}">Добавить</a></div><div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></section>'
    out+='<h2 class="section-title">Представления только для просмотра</h2>'
    for n in ['v_order_summary','v_popular_products','v_customer_orders','v_product_ratings','v_daily_sales']:
        rows=c.execute(f'SELECT * FROM {n} LIMIT 20').fetchall(); cols=list(rows[0].keys()) if rows else []; out+=f'<section class="panel"><h2>{n}</h2><div class="table-wrap"><table><thead><tr>'+''.join(f'<th>{x}</th>' for x in cols)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{esc(r[x])}</td>' for x in cols)+'</tr>' for r in rows)+'</tbody></table></div></section>'
    return out
class Handler(BaseHTTPRequestHandler):
    def send(self,data,status=200,ctype='text/html; charset=utf-8',cookie=None):
        b=data.encode() if isinstance(data,str) else data; self.send_response(status); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(b))); 
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path); u=user(self)
        if p.path == '/api/products':
            c=db(); rows=c.execute('SELECT id,name,category,description,price,image_url,is_active FROM products WHERE is_active=1 ORDER BY id').fetchall(); c.close()
            self.send(json.dumps([dict(r) for r in rows], ensure_ascii=False), ctype='application/json; charset=utf-8'); return
        if p.path.startswith('/static/'):
            rel=p.path[len('/static/'):].replace('/',os.sep); f=os.path.abspath(os.path.join(STATIC,rel))
            if not f.startswith(os.path.abspath(STATIC)+os.sep): return
            if os.path.exists(f):
                ctype='text/css' if f.endswith('.css') else 'application/javascript' if f.endswith('.js') else 'image/jpeg' if f.endswith('.jpg') else 'image/png'
                self.send(open(f,'rb').read(),ctype=ctype);return
        c=db(); n=parse_qs(p.query).get('page',['home'])[0]
        if n=='admin' and (not u or u['role']!='admin'): body='<section class="empty"><h1>Доступ закрыт</h1><a class="button" href="/?page=login">Войти</a></section>'
        elif n=='home':body=home(c)
        elif n=='catalog':body=catalog(c)
        elif n in ('login','register'):body=auth(n)
        elif n=='account' and u:body=account(c,u)
        elif n=='account':body=auth('login')
        elif n=='admin':body=admin(c)
        elif n=='crud' and u and u['role']=='admin':
            t=parse_qs(p.query).get('table',[''])[0]; eid=parse_qs(p.query).get('edit',[None])[0]; body=crud_form(c,t,int(eid) if eid else None) if t in CRUD_TABLES else '<section class="empty"><h1>Неизвестная таблица</h1></section>'
        elif n=='builder':body=builder()
        elif n in ('delivery','reviews','contacts','cart'):body=info_page(n)
        else:body='<section class="empty"><h1>Flowers Studio</h1><p>Доставка по Москве и области ежедневно с 9:00 до 21:00.</p></section>'
        self.send(shell(n,body,u)); c.close()
    def do_POST(self):
        q=urlparse(self.path); d={k:v[0] for k,v in parse_qs(self.rfile.read(int(self.headers.get('Content-Length',0))).decode()).items()}; c=db(); a=parse_qs(q.query).get('action',[''])[0]
        if a=='crud' and user(self) and user(self)['role']=='admin':
            t=d.get('table'); ident=d.get('id'); mode=d.get('crud')
            if t in CRUD_TABLES:
                cols=[x[1] for x in c.execute(f'PRAGMA table_info({t})') if x[1] not in ('id','created_at')]
                if mode=='delete': c.execute(f'DELETE FROM {t} WHERE id=?',(ident,))
                else:
                    values=[d.get(x,'') for x in cols]
                    if mode=='update': c.execute(f'UPDATE {t} SET '+','.join(f'{x}=?' for x in cols)+' WHERE id=?',values+[ident])
                    else: c.execute(f'INSERT INTO {t} ('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+')',values)
                c.commit(); self.send('<meta http-equiv="refresh" content="0;url=/?page=admin">Сохранено'); return
        if a in ('login','register'):
            email=d.get('email','').strip().lower(); row=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            if a=='register' and not row:c.execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',(d.get('name','Гость'),email,pwd(d.get('password',''))));c.commit();row=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            if row and row['password_hash']==pwd(d.get('password','')):sid=secrets.token_urlsafe(24);SESSIONS[sid]=dict(row);self.send('<!doctype html><html><head><meta http-equiv="refresh" content="0;url=/?page=account"></head><body>Выполняется вход…</body></html>',cookie=f'sid={sid}; Path=/; HttpOnly; SameSite=Lax');return
        self.send(shell('Ошибка','<section class="empty"><h1>Не удалось выполнить действие</h1><a class="button" href="/?page=login">Вернуться</a></section>',None),400);c.close()
if __name__=='__main__':init_db();print('Flowers app: http://127.0.0.1:8765');ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
