const output = document.getElementById("output");
const body = document.querySelector("body");
const columns = {
    word: 1,
    meaning: 2,
    language: 3,
    login: 4
}



async function makeAndSendRequest(e, endpoint, method, formId) { // асинхронная функция (быстро переключается между задачами, не ждет, пока запрос выполнится)
    e.preventDefault();
    let form = document.getElementById(formId);
    let formData = new FormData(form);
    let params = new URLSearchParams();
    // отсеиваем пустые параметры
    for (let [key, value] of formData.entries()) {
        if (value.trim() !== "") {
            params.append(key, value);
        }
    }
    console.log(params);

    let url=`/${endpoint}?${params.toString()}`; // endpoint - куда прилетит запрос (название функции из python)

        let response = await fetch(url, {method}); // пытаемся кинуть запрос (ответ либо 200, либо 400)
        // функция на отправление запроса в api, получаем Promise - обещание выполнить запрос
        // await - возможно ожидание, можно переключаться на другие задачи в функции, пока запрос не выполнится
        let result = await response.json(); // json
        output.innerHTML = "";
        if (url.startsWith("/see")) {
            createTable(result);
        } else {
            createPre(result);
        }


        console.log(result);
        // output.innerText = result; // результат пишем в output
        // проверяем статус код
        if (response.ok) {
            // УСПЕХ!
            output.style.borderColor = " #57CD89";
            output.style.backgroundColor = "#EDFAF2";
        } else {
            output.style.borderColor = "#EE253D";
            output.style.backgroundColor = "#FDE9EB";
        }
}


function createTable(result) {
    let table = document.createElement("table");
    if (!result || result.length === 0) {
        output.innerText = "Нет данных";
        console.log(">>", result);
        return;
    }

    // Создание заголовка таблицы
    let thead = document.createElement("thead");
    let headerRow = document.createElement("tr");
    headerRow.innerHTML = '<th>Слово</th><th>Значение</th><th>Язык заимствования</th><th>Кто добавил</th>';
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Создание тела таблицы
    let tbody = document.createElement("tbody");
    result['Результат'].forEach(item => {
        let tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${item[columns.word]}</td>
            <td>${item[columns.meaning]}</td>
            <td>${item[columns.language]}</td>
            <td>${item[columns.login]}</td>
        `;
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    output.appendChild(table);
}

function createPre(result) {
    let pre = document.createElement("pre");
    pre.innerText = JSON.stringify(result, null, 2);
    output.appendChild(pre);
}