const pre = document.getElementById("output")
const body = document.querySelector("body")


async function sendRequest(url, method) { // асинхронная функция (быстро переключается между задачами, не ждет, пока запрос выполнится)
    let response = await fetch(url, {method}); // функция на отправление запроса в api, получаем Promise - обещание выполнить запрос
    // await - возможно ожидание, можно переключаться на другие задачи в функции, пока запрос не выполнится
    let res = await response.json();
    return res
}

async function makeAndSendRequest(e, endpoint, method, formId) {
    e.preventDefault();
    let form = document.getElementById(formId);
    let formData = new FormData(form);
    let params = new URLSearchParams(formData);
    let url=`/${endpoint}?${params.toString()}`;
    
    try {
        let result = await sendRequest(url, method); // пытаемся кинуть запрос
        // УСПЕХ!
        pre.innerHTML = JSON.stringify(result, null, 2);
        pre.style.borderColor = " #57CD89";
        body.style.backgroundColor = "#EDFAF2";
    } catch (error) {
        console.log(error);
        pre.innerText = "Ошибка";
    }
}
// endpoint - куда прилетит запрос (название функции из python)
function addWord() {

}