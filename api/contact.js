// api/contact.js — приём заявок с формы и отправка в Telegram
// Vercel Serverless Function (Node.js ESM)
//
// Требуемые переменные окружения (Vercel → Settings → Environment Variables):
//   TELEGRAM_BOT_TOKEN — токен бота от @BotFather
//   TELEGRAM_CHAT_ID   — ID чата/группы, куда слать заявки

export default async function handler(req, res) {
  // CORS не нужен — фронт и API на одном домене. Только POST.
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name = '', phone = '', comment = '' } = req.body || {};

  // --- Валидация ---
  const cleanPhone = String(phone).trim();
  const digits = cleanPhone.replace(/\D/g, '');
  if (digits.length < 10 || digits.length > 12) {
    return res.status(400).json({ error: 'Некорректный телефон' });
  }

  const cleanName = String(name).trim().slice(0, 100);
  const cleanComment = String(comment).trim().slice(0, 1000);

  // --- Примитивная защита от спама ---
  // Honeypot: если фронт когда-нибудь добавит скрытое поле website — боты его заполнят
  if (req.body?.website) {
    return res.status(200).json({ ok: true }); // делаем вид, что приняли
  }

  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chatId) {
    console.error('TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID не заданы');
    return res.status(500).json({ error: 'Server misconfigured' });
  }

  // --- Сообщение ---
  const now = new Date().toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' });
  const text = [
    '🐔 <b>Новая заявка с сайта ОМСЧИКЕН</b>',
    '',
    cleanName ? `👤 Имя: <b>${escapeHtml(cleanName)}</b>` : null,
    `📞 Телефон: <b>${escapeHtml(cleanPhone)}</b>`,
    cleanComment ? `💬 Комментарий: ${escapeHtml(cleanComment)}` : null,
    '',
    `🕐 ${now} МСК`
  ].filter(Boolean).join('\n');

  try {
    const tgRes = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        parse_mode: 'HTML'
      })
    });

    if (!tgRes.ok) {
      const err = await tgRes.text();
      console.error('Telegram API error:', err);
      return res.status(502).json({ error: 'Не удалось отправить заявку' });
    }

    return res.status(200).json({ ok: true });
  } catch (e) {
    console.error('contact handler error:', e);
    return res.status(500).json({ error: 'Внутренняя ошибка' });
  }
}

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
