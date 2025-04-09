// Функция для получения CSRF-токена из cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Функция для обновления блока с данными через GET-запрос
function EntityOneUpdateBlock(url) {
    const contentBlock = $("#dynamic-block");
    $.ajax({
        url: url,
        type: 'GET',
        contentType: 'application/json',
        success: function(data) {
            contentBlock.html(data.html);
        },
        error: function(xhr, status, error) {
            contentBlock.html(`<p class="text-danger">Ошибка: ${error}</p>`);
        }
    });
}

// Функция для отправки данных формы через POST-запрос
function submitForm() {
    const form = $('#entity-form');
    if (!form.length) {
        console.error('Элемент с id="entity-form" не найден');
        return;
    }
    
    const formData = form.serialize(); // Сериализуем данные формы

    const csrfToken = getCookie('csrftoken');
    $.ajax({
        url: '/entity/create/',
        type: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        data: formData, // Отправляем сериализованные данные формы
        success: function(response) {
            console.log('Данные успешно отправлены:', response);
        },
        error: function(xhr, status, error) {
            console.error("Ошибка при загрузке данных:", error);
        }
    });
}