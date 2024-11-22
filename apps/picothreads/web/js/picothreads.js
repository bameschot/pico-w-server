let isEditing = false
let usersCache = {}

async function loginUser(userName, password) {
    return await buildPostUserLoginRequest(baseUri, userName, password)
        .then(async response => {
            if (await handleErrorResponses(response)) {
                console.log("failure to login user")
                return false
            }
            console.log("logging in user")

            json = await response.json()
            console.log(JSON.stringify(json))
            setUserCookies(userName, json.userId, json.token)
            console.log("Login user")
            return true
        })
}

async function refreshUserToken() {
    if (isUserTokenCookieSet()) {
        await buildGetUserTokenRefreshRequest(baseUri)
            .then(async response => {
                if (await handleErrorResponses(response))
                    return

                json = await response.json()
                setUserTokenCookie(json.token)
                console.log("User token refreshed")
            })
    }
}

async function logoutUser() {
    await buildPostUserLogoutRequest(baseUri)
        .then(response => {
            handleErrorResponses(response)
        })
}

async function listThreads() {
    if (isUserTokenCookieSet() && !isEditing) {
        await buildGetThreadsRequest(baseUri)
            .then(async response => {
                if (await handleErrorResponses(response))
                    return

                json = await response.json()
                document.getElementById("threads-container-div").innerHTML = renderThreadsHtml(json.threads)
            })
    }
}

async function postUpdateMessage(threadId, messageId) {
    let text = document.getElementById('update-message-input-' + threadId + '-' + messageId).value

    console.log("Sending Message: " + text)

    buildPostUpdateMessageRequest(baseUri, threadId, messageId, text)
        .then(async response => {
            if (await handleErrorResponses(response))
                return

            json = await response.json()
            document.getElementById("threads-container-div").innerHTML = renderThreadsHtml(json.threads)
        })
    console.log("Updated message for thread: " + threadId)
}

async function postNewMessage(threadId) {
    let text = document.getElementById('new-message-input-' + threadId).value

    console.log("Sending Message: " + text)

    buildPostMessageRequest(baseUri, threadId, text)
        .then(async response => {
            if (await handleErrorResponses(response))
                return

            json = await response.json()
            document.getElementById("threads-container-div").innerHTML = renderThreadsHtml(json.threads)
        })
    console.log("New message for thread: " + threadId)
}


async function postNewThread() {
    console.log("New thread")
    let subject = document.getElementById("new-thread-input").value
    buildPostThreadsRequest(baseUri, subject)
        .then(async response => {
            if (await handleErrorResponses(response))
                return

            json = await response.json()
            document.getElementById("threads-container-div").innerHTML = renderThreadsHtml(json.threads)
        })
}

async function getFetchUsers() {
    if (isUserTokenCookieSet()) {
        await buildGetUsersRequest(baseUri)
            .then(async response => {
                if (await handleErrorResponses(response))
                    return

                json = await response.json()

                usersCache = json.users
                let userList = "<div class='user-list'>"
                for (let user of json.users) {
                    userList += "<div class='user'>"
                    let userLastLogonDiff = getEpochSeconds() - user.lastOnlineTs

                    if (userLastLogonDiff <= 180)
                        userList += "&#x1F7E2 " + user.userName
                    else if (userLastLogonDiff > 180 && userLastLogonDiff < 900) {
                        userList += "&#x1F7E1 " + user.userName
                    } else {
                        userList += "&#x1F534 " + user.userName
                    }
                    userList += "</div>"
                }
                userList += "</div>"
                document.getElementById("online-users-div").innerHTML = userList
            })
    }
}

function postSetCharacterCounter(event, textFieldId, characterCounterId, maxCharacters) {
    let textFieldElement = document.getElementById(textFieldId)
    if (textFieldElement != null) {
        document.getElementById(characterCounterId).innerHTML = "(" + textFieldElement.value.length + " / " + maxCharacters + ")"
    }
}

async function handleErrorResponses(response) {
    if (response.status === 401) {
        await clearUser()
        json = await response.json()
        showError(json.details)
        return true
    } else if (!(response.status === 201 || response.status === 200)) {
        json = await response.json()
        showError(json.details)
        return true
    }
    return false
}

function showError(message) {
    document.getElementById('error-msg-item').innerHTML = message
    document.getElementById('error-container').style.display = "block"

    setTimeout(hideError, 5000)
}

function hideError() {
    document.getElementById('error-msg-item').innerHTML = ""
    document.getElementById('error-container').style.display = "none"
}

async function landingPage() {
    if (isUserTokenCookieSet()) {
        console.log("User cookie set")
        await getFetchUsers()
        await listThreads()

        setState(STATES.DEFINED_USER_ID)

        logoutButton = document.getElementById("logout-user-button")
        logoutButton.style.display = "block"
        logoutButton.innerHTML = "Logout " + getCookie(USER_NAME_COOKIE)
    } else {
        console.log("No User cookie set")
        setState(STATES.NO_USER_ID)
    }
}

async function setUser() {
    let userName = document.getElementById("user-name-input").value
    let seed = document.getElementById("user-seed-input").value

    if (await loginUser(userName, seed)) {
        await getFetchUsers()
        await listThreads()

        let logOutButton = document.getElementById("logout-user-button")
        logOutButton.style.display = "block"
        logOutButton.innerHTML = "Logout " + getCookie(USER_NAME_COOKIE)

        setState(STATES.DEFINED_USER_ID)
    }
}

async function clearUser() {
    console.log("logging out user")
    document.getElementById("logout-user-button").style.display = "none"
    document.getElementById("threads-container-div").innerHTML = ""

    if (isUserTokenCookieSet())
        await logoutUser()

    clearUserCookies()
    await landingPage()
}

function setIsEditing() {
    console.log("set editing flag")
    isEditing = true
}

function clearIsEditing() {
    console.log("clear editing flag")
    isEditing = false
}

function setUpdateMessage(threadId, messageId) {
    console.log("Start editing message: " + messageId + " for thread " + threadId)

    document.getElementById("message-edit-container-" + messageId).style.display = "table"
    document.getElementById("message-view-container-" + messageId).style.display = "none"

    document.getElementById('update-message-input-' + threadId + '-' + messageId).value = document.getElementById("message-text-container-" + messageId).innerHTML
    setIsEditing()

}

function processUserReferences(text) {
    for (let key in usersCache) {
        userName = usersCache[key].userName
        text = text.replaceAll("@" + userName, '<span class="userReference">@' + userName + '</span>')
    }
    return text
}


/*
--------------
 */

/*
THREADS
 */
function buildGetThreadsRequest(baseUri) {
    let uriGetThreads = baseUri + "/pico-threads/threads"
    console.log("Fetching users: " + uriGetThreads)

    return fetch(uriGetThreads, {
        method: "GET",
        mode: "cors",
        headers: {"Authorization": createBearerAuthValue(getCookie(USER_TOKEN_COOKIE))}
    })
}

function buildPostThreadsRequest(baseUri, subject) {
    let uriNewThread = baseUri + "/pico-threads/threads"
    console.log("Creating new thread: " + uriNewThread)

    return fetch(uriNewThread, {
        method: "POST",
        mode: "cors",
        headers: {
            "Authorization": createBearerAuthValue(getCookie(USER_TOKEN_COOKIE)),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "subject": subject,
            "by": getCookie(USER_NAME_COOKIE)
        })
    })
}

function buildPostMessageRequest(baseUri, threadId, text) {

    let uriNewMessage = baseUri + "/pico-threads/threads/" + threadId + "/messages"
    console.log("Creating new thread: " + uriNewMessage)

    let jsonBody = JSON.stringify({
        "text": text,
        "by": getCookie(USER_NAME_COOKIE)
    })
    console.log(jsonBody)

    return fetch(uriNewMessage, {
        method: "POST",
        mode: "cors",
        headers: {
            "Authorization": createBearerAuthValue(getCookie(USER_TOKEN_COOKIE)),
            'Content-Type': 'application/json'
        },
        body: jsonBody
    })
}

function buildPostUpdateMessageRequest(baseUri, threadId, messageId, text) {

    let uriUpdateMessage = baseUri + "/pico-threads/threads/" + threadId + "/messages/" + messageId
    console.log("updating thread: " + uriUpdateMessage)


    let jsonBody = JSON.stringify({
        "text": text,
        "by": getCookie(USER_NAME_COOKIE)
    })
    console.log(jsonBody)

    return fetch(uriUpdateMessage, {
        method: "POST",
        mode: "cors",
        headers: {
            "Authorization": createBearerAuthValue(getCookie(USER_TOKEN_COOKIE)),
            'Content-Type': 'application/json'
        },
        body: jsonBody
    })
}

//
//
//


function replaceLineBreaksHtml(threadId) {
    setIsEditing()
    document.getElementById(threadId).value = document.getElementById(threadId).value.replaceAll('\n', "\n<br>")
}

function insertBlockQuoteHtml(threadId) {
    setIsEditing()
    document.getElementById(threadId).value +=
        '<blockquote>\n' +
        '\n' +
        '</blockquote>'
}

function insertCodeHtml(threadId) {
    setIsEditing()
    document.getElementById(threadId).value +=
        '<code>\n' +
        '\n' +
        '</code>'
}

function insertColorHtml(threadId) {
    setIsEditing()
    document.getElementById(threadId).value +=
        '<span style="color: darkgreen; font-size: xx-small">\n' +
        '\n' +
        '</span>'
}

function insertListHtml(threadId) {
    setIsEditing()
    document.getElementById(threadId).value +=
        '<ul style="text-align: left">\n' +
        '<li> </li>\n' +
        '<li> </li>\n' +
        '</ul>'
}

async function keyPressedEditMessage(event, threadId, messageId) {
    if (event.charCode === 13 && (event.shiftKey || event.ctrlKey)) { //enter + (shift | ctrl)
        if (messageId === 'null') {
            document.getElementById('new-message-input-' + threadId).value += "<br>"
        } else {
            document.getElementById('update-message-input-' + threadId + '-' + messageId).value += "<br>"
        }
    } else if (event.charCode === 13) {
        if (messageId === 'null') {
            await postNewMessage(threadId)
        } else {
            await postUpdateMessage(threadId, messageId)
        }
    }
}

async function keyPressedNewThread(event) {
    if (event.charCode === 13) { //enter
        await postNewThread()
    }
}

function renderSeparator() {
    return "<div class='thread-separator'></div>"
}

function renderThreadsHtml(threads) {
    //            https://www.w3schools.com/howto/howto_js_treeview.asp
    let html = "<div class='threads-container'>"
    //html += "Threads"
    for (let thread of threads) {
        html += renderThreadHtml(thread)
        html += renderSeparator()
    }
    html += renderSeparator()
    html += renderNewThreadInput()
    html += "</div>"
    return html
}

function renderThreadHtml(thread) {
    let bySelfClass = ""
    //let bySelfClass = (thread.createdBySelf) ? "bySelf" : "";

    let html = "<div class='thread-container " + bySelfClass + "'>"
    html += "<div class='thread-subject-container'>" + thread.subject + " </div>"
    html += "<div class='thread-by-container'>" + thread.startedBy + " (" + timestampToDate(thread.timestamp) + ") </div>"
    for (let message of thread.messages) {
        html += renderMessageHtml(thread.threadId, message)
        html += renderSeparator()
    }
    html += renderNewMessageInput(thread.threadId, null)
    html += "</div>"
    return html
}

function renderMessageHtml(threadId, message) {
    let isBySelf = (getCookie(USER_ID_COOKIE) === message.byId)
    let bySelfClass = isBySelf ? "bySelf" : "";

    let html = '<div id="message-wrapper-' + message.messageId + '" style="display: table; width: 100%">'
    html += '<div id="message-view-container-' + message.messageId + '" class="message-view-container ' + bySelfClass + '">'

    html += '<div class="message-by-container" style="display: table; width: 100%">'
    html += '<div style="float: left">' + message.by + ' (' + timestampToDate(message.timestamp) + ')' + ((message.editedTimestamp > 0) ? ' edited: (' + timestampToDate(message.timestamp) + ')' : '') + '</div>'
    if (isBySelf) {
        html += '<button style="float: right" class="edit-html-button" onclick="setUpdateMessage(\'' + threadId + '\',\'' + message.messageId + '\')">edit</button>'
    }
    html += '</div>'

    html += '<div id="message-text-container-' + message.messageId + '" class="message-text-container" >' + processUserReferences(message.text) + '</div>'
    html += '</div>'

    if (isBySelf) {
        html += '<div id="message-edit-container-' + message.messageId + '" class="message-view-container ' + bySelfClass + ' " style="display: none">'
        html += renderNewMessageInput(threadId, message.messageId)
        html += '</div>'
    }

    html += '</div>'
    return html
}

function renderNewMessageInput(threadId, messageId) {

    let inputFieldId
    let characterCounterId
    if (messageId == null) {
        inputFieldId = 'new-message-input-' + threadId
        characterCounterId = 'new-message-input-counter-' + threadId
    } else {
        inputFieldId = 'update-message-input-' + threadId + '-' + messageId
        characterCounterId = 'update-message-input-counter-' + threadId + '-' + messageId
    }

    let html = ""
    html += "<div class='new-message-container'>"

    html += '<div class="new-item" style="width: 100%; float: left">'
    html += '<textarea maxlength="' + maxMessageCharacters + '" style="font-size: small; vertical-align: center; width: 100%;" id="' + inputFieldId + '" onfocus="setIsEditing()" onblur="clearIsEditing()" onkeypress="keyPressedEditMessage(event,\'' + threadId + '\',\'' + messageId + '\')" onInput="postSetCharacterCounter(event,\'' + inputFieldId + '\',\'' + characterCounterId + '\',\'' + maxMessageCharacters + '\')"></textarea>'


    html += '<button class = "edit-html-button" onclick="insertBlockQuoteHtml(\'' + inputFieldId + '\')">quote</button>&nbsp'
    html += '<button class = "edit-html-button" onclick="insertCodeHtml(\'' + inputFieldId + '\')">code</button>&nbsp'
    html += '<button class = "edit-html-button" onclick="insertColorHtml(\'' + inputFieldId + '\')">colour</button>&nbsp'
    html += '<button class = "edit-html-button" onclick="insertListHtml(\'' + inputFieldId + '\')">list</button>&nbsp'
    html += '<button class = "edit-html-button" onclick="replaceLineBreaksHtml(\'' + inputFieldId + '\')">br</button>&nbsp'

    if (messageId == null)
        html += '<button class="edit-html-button" style="vertical-align: top; float: right" id="new-message-button-' + threadId + '" onclick="postNewMessage(\'' + threadId + '\')">></button>'
    else
        html += '<button class="edit-html-button" style="vertical-align: top; float: right" id="update-message-button-' + threadId + '" onclick="postUpdateMessage(\'' + threadId + '\',\'' + messageId + '\')">+</button>'

    html += '<div id="' + characterCounterId + '" class="new-item-counter" style="padding-top: 4%; padding-right: 1%; float: right;">(0/' + maxMessageCharacters + ')</div>'
    html += '</div>'

    html += "</div>"

    return html
}

function renderNewThreadInput() {
    let inputFieldId = 'new-thread-input'
    let characterCounterId = 'new-thread-input-counter'

    let html = ""

    html += "<div class='thread-subject-container'>{New Thread}</div>"
    html += "<div class='new-thread-container'>"
    html += '<div class="new-item" style="width: 70%; float: left">'
    html += '<input maxlength="' + maxThreadSubjectCharacters + '" type="text" style="vertical-align: center; width: 115%;" id="' + inputFieldId + '" onfocus="setIsEditing()" onblur="clearIsEditing()" onkeypress="keyPressedNewThread(event)" onInput="postSetCharacterCounter(event,\'' + inputFieldId + '\',\'' + characterCounterId + '\',\'' + maxThreadSubjectCharacters + '\')"></input>'
    html += '</div>'
    html += '<div class="new-item" style="width: 17%; float: right; font-size: xx-small"/>'
    html += '<div id="' + characterCounterId + '" class="new-item" style="float: right;">(0/' + maxThreadSubjectCharacters + ')</div>'
    html += '</div>'
    html += '<div class="new-item" style="width: 8%; float: right">'
    html += '<button class="edit-html-button" style="vertical-align: top" id="new-thread-button" onclick="postNewThread()">></button>'
    html += "</div>"
    html += "</div>"

    return html
}
