import re,io,datetime,urllib.request,os,sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

script_dir=os.path.dirname(os.path.abspath(__file__))
raw=open(os.path.join(script_dir,'price-data.js'),encoding='utf-8').read()

def gf(k,t):
    m=re.search(rf"{k}\s*:\s*'([^']*)'",t)
    return m.group(1) if m else ''

def gp(t):
    rows=re.findall(r"\{\s*name\s*:\s*'([^']+)'\s*,\s*desc\s*:\s*'([^']+)'\s*,\s*price\s*:\s*'([^']+)'\s*,\s*hit\s*:\s*(true|false)\s*,\s*active\s*:\s*(true|false)",t)
    return [{'name':n,'desc':d,'price':p,'hit':h=='true','active':a=='true'} for n,d,p,h,a in rows]

co={'phone':gf('phone',raw),'person':gf('person',raw),'telegram':gf('telegram',raw),
    'email':gf('email',raw),'inn':gf('inn',raw),'ogrn':gf('ogrn',raw),'site':gf('site',raw)}
m=re.search(r"min_order\s*:\s*'([^']*)'",raw)
co['min_order']=m.group(1) if m else 'от 500 кг'
products=[p for p in gp(raw) if p['active']]
print(f'✓  Загружено {len(products)} позиций')

FD='/System/Library/Fonts/Supplemental/'
for a,n in [('R','Arial.ttf'),('B','Arial Bold.ttf'),('SR','Times New Roman.ttf'),('SB','Times New Roman Bold.ttf'),('M','Courier New.ttf')]:
    p=FD+n
    if os.path.exists(p): pdfmetrics.registerFont(TTFont(a,p))

WHITE=(1,1,1);BG_PAGE=(0.97,0.96,0.98);BG_ROW=(0.93,0.91,0.97)
DARK=(0.06,0.01,0.18);PURPLE=(0.18,0.10,0.45);GOLD=(0.82,0.55,0.02)
ORANGE=(0.78,0.36,0.01);MUTED=(0.45,0.40,0.60);BORDER=(0.80,0.76,0.90);GREEN=(0.30,0.78,0.48)

W,H=A4
today=datetime.date.today().strftime('%d.%m.%Y')
out=os.path.join(script_dir,'omschicken-price.pdf')
c=canvas.Canvas(out,pagesize=A4)
c.setTitle('ОМСЧИКЕН — Прайс-лист')

def rr(x,y,w,h,r=6,fc=None,sc=None,lw=0.5):
    if fc: c.setFillColorRGB(*fc)
    if sc: c.setStrokeColorRGB(*sc);c.setLineWidth(lw)
    p=c.beginPath()
    p.moveTo(x+r,y);p.lineTo(x+w-r,y);p.arcTo(x+w-r,y,x+w,y+r,-90,90)
    p.lineTo(x+w,y+h-r);p.arcTo(x+w-r,y+h-r,x+w,y+h,0,90)
    p.lineTo(x+r,y+h);p.arcTo(x,y+h-r,x+r,y+h,90,90)
    p.lineTo(x,y+r);p.arcTo(x,y,x+r,y+r,180,90);p.close()
    c.drawPath(p,fill=1 if fc else 0,stroke=1 if sc else 0)

c.setFillColorRGB(*BG_PAGE);c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColorRGB(*DARK);c.rect(0,H-130,W,130,fill=1,stroke=0)

try:
    data=urllib.request.urlopen(f"https://{co['site']}/img/logo.png",timeout=6).read()
    c.drawImage(ImageReader(io.BytesIO(data)),W-118,H-118,width=105,height=105,mask='auto')
    print('✓  Логотип загружен')
except Exception as e: print(f'⚠  Логотип: {e}')

c.setFont('M',8);c.setFillColorRGB(*MUTED);c.drawString(32,H-22,'ПРАЙС-ЛИСТ · КУРИНОЕ МЯСО ОПТОМ')
c.setFont('SB',28);c.setFillColorRGB(*WHITE);c.drawString(32,H-58,'ОМСЧИКЕН')
c.setFillColorRGB(*GOLD);c.rect(32,H-64,160,2.5,fill=1,stroke=0)
c.setFont('R',10);c.setFillColorRGB(0.7,0.65,0.85)
c.drawString(32,H-80,'Напрямую с птицефабрик  ·  ФГИС «Меркурий»  ·  Безнал, НДС')

bx=32
for txt in [co['min_order'],'Отгрузка 2 суток','Вся Россия']:
    tw=c.stringWidth(txt,'B',9);rr(bx,H-118,tw+20,22,r=5,fc=PURPLE)
    c.setFont('B',9);c.setFillColorRGB(*GOLD);c.drawString(bx+10,H-110,txt);bx+=tw+34

c.setFont('R',8);c.setFillColorRGB(0.6,0.55,0.75);c.drawString(32,H-128,f'Актуально на {today}')

ROW=34;TY=H-148;cols=[24,50,196,400,510]
rr(20,TY-22,W-40,26,r=5,fc=DARK)
c.setFont('B',8);c.setFillColorRGB(*GOLD)
for lbl,cx in zip(['№','Наименование','Описание','Цена'],cols[:4]):
    c.drawString(cx+4,TY-13,lbl)

y=TY-22
for i,p in enumerate(products):
    y-=ROW
    rr(20,y,W-40,ROW,r=0,fc=WHITE if i%2==0 else BG_ROW)
    if p['hit']: c.setFillColorRGB(*ORANGE);c.rect(20,y,4,ROW,fill=1,stroke=0)
    c.setStrokeColorRGB(*BORDER);c.setLineWidth(0.3);c.line(20,y+ROW,W-20,y+ROW)
    c.setFont('M',8);c.setFillColorRGB(*MUTED);c.drawString(cols[0]+4,y+11,f'{i+1:02d}')
    if p['hit']:
        rr(cols[1]+4,y+20,26,11,r=3,fc=ORANGE)
        c.setFont('B',6.5);c.setFillColorRGB(*WHITE);c.drawString(cols[1]+7,y+23,'ХИТ')
    c.setFont('B',10);c.setFillColorRGB(*DARK);c.drawString(cols[1]+4,y+10,p['name'])
    c.setFont('R',8);c.setFillColorRGB(*MUTED);c.drawString(cols[2]+4,y+11,p['desc'])
    c.setFont('B',13);c.setFillColorRGB(*ORANGE);c.drawRightString(cols[4]-6,y+10,p['price'].replace('₽','руб.'))

y-=ROW
rr(20,y,W-40,ROW,r=4,fc=BG_ROW,sc=BORDER,lw=0.5)
c.setFont('B',9);c.setFillColorRGB(*PURPLE);c.drawString(cols[1]+4,y+11,'Другие позиции — по запросу')
c.setFont('R',8);c.setFillColorRGB(*MUTED);c.drawRightString(cols[4]-6,y+11,f"→ {co['site']}")

c.setFillColorRGB(*DARK);c.rect(0,0,W,68,fill=1,stroke=0)
c.setFillColorRGB(*GOLD);c.rect(0,68,W,1.5,fill=1,stroke=0)
for val,lbl,x in [(co['phone'],co['person'],24),(co['telegram'],'Telegram-канал',210),(co['email'],'Почта',390)]:
    c.setFont('B',9);c.setFillColorRGB(*GOLD);c.drawString(x,52,val)
    c.setFont('R',7);c.setFillColorRGB(0.55,0.50,0.70);c.drawString(x,40,lbl)
c.setFont('M',7);c.setFillColorRGB(0.30,0.25,0.50)
c.drawRightString(W-20,28,f"ООО ОМСЧИКЕН · ИНН {co['inn']} · ОГРН {co['ogrn']}")
c.drawRightString(W-20,18,f'Прайс-лист действителен на дату формирования · {today}')
c.save()
print(f'✓  PDF сохранён: {out}')
