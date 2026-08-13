// Inicializar la Mini App de Telegram
const tg = window.Telegram.WebApp;
tg.expand(); // Expandir a pantalla completa

// Obtener datos del usuario de Telegram
const user = tg.initDataUnsafe.user;
if (user) {
    document.getElementById('user-info').innerHTML = `
        Hola, ${user.first_name}!<br>
        <small>@${user.username || 'sin usuario'}</small>
    `;
    // Aquí podrías consultar el saldo del usuario vía API
    fetch(`/api/wallet/balance/${user.id}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('balance').textContent = `💰 Saldo: $${data.balance || 0} MXN`;
        })
        .catch(() => {});
}

// Botón de donación
document.getElementById('btn-donar').addEventListener('click', () => {
    tg.showPopup({
        title: 'Donación',
        message: '¡Gracias por apoyar NeuraforgeAI!',
        buttons: [{ type: 'ok' }]
    });
});

// Botón de cerrar
document.getElementById('btn-cerrar').addEventListener('click', () => {
    tg.close();
});

// Notificar a Telegram que la app está lista
tg.ready();
