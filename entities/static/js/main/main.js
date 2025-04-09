let loadingHtml = `    <div class="container">

        <div class="h1Container">
      
          <div class="cube h1 w1 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h1 w1 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h1 w1 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h1 w2 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h1 w2 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h1 w2 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h1 w3 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h1 w3 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h1 w3 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
        </div>
        
        <div class="h2Container">
      
          <div class="cube h2 w1 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h2 w1 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h2 w1 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h2 w2 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h2 w2 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h2 w2 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h2 w3 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h2 w3 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h2 w3 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
        </div>
        
        <div class="h3Container">
      
          <div class="cube h3 w1 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h3 w1 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h3 w1 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h3 w2 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h3 w2 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h3 w2 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h3 w3 l1">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h3 w3 l2">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
      
          <div class="cube h3 w3 l3">
            <div class="face top"></div>
            <div class="face left"></div>
            <div class="face right"></div>
          </div>
        </div>
        
      </div>`

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
    contentBlock.html(loadingHtml);
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
function submitForm(url) {
  const form = $('#entity-form');
  if (!form.length) {
      console.error('Элемент с id="entity-form" не найден');
      return;
  }
  
  const formData = Object.fromEntries(new FormData(form[0]).entries());
  const csrfToken = getCookie('csrftoken');

  $.ajax({
      url: url,
      type: 'POST',
      headers: {
          'X-CSRFToken': csrfToken
      },
      contentType: 'application/json',
      data: JSON.stringify(formData),
      success: function(response) {
          console.log('Данные успешно отправлены:', response);
      },
      error: function(xhr, status, error) {
          console.error("Ошибка при загрузке данных:", error);
          console.log("Ответ сервера:", xhr.responseText);
      }
  });
}