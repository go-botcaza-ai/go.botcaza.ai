// Inicializar la Mini App
const tg = window.Telegram.WebApp;
tg.expand(); // Expandir a pantalla completa

function saludar() {
    const user = tg.initDataUnsafe.user;
    const nombre = user ? user.first_name : 'Visitante';
    tg.showAlert(`¡Hola, ${nombre}! Bienvenido a NeuraforgeAI.`);
}

// Notificar a Telegram que la app está lista
tg.ready();
