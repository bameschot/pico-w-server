
/*
SECURE MODE
 */
IS_SECURE_MODE = window.crypto.subtle != null

/*
STATE
 */

let STATES = {
    UNDEF: "undefined-div",
}

let CURRENT_STATE = STATES[0]

function setState(state) {
    CURRENT_STATE = state
    console.log("Transitioning to state: " + CURRENT_STATE)
    showOneElement(CURRENT_STATE, elements)
}

function showOneElement(visibleElementId, elementIds) {

    elementIds.forEach(elementId => {
        if (visibleElementId === elementId) {
            document.getElementById(elementId).style.display = "block"
        } else {
            document.getElementById(elementId).style.display = "none"
        }
    })
}


/*
USER
 */
const USER_ID_COOKIE = "USER_ID"
const USER_NAME_COOKIE = "USER_NAME"
const USER_TOKEN_COOKIE = "USER_TOKEN"

function isUserTokenCookieSet() {
    return getCookie(USER_TOKEN_COOKIE).length > 0
}

function setUserCookies(userName, userId, token) {
    document.cookie = USER_ID_COOKIE + "=" + userId + "; expires=Thu, 13 May 2099 12:00:00 UTC"
    document.cookie = USER_NAME_COOKIE + "=" + userName + "; expires=Thu, 13 May 2099 12:00:00 UTC"
    document.cookie = USER_TOKEN_COOKIE + "=" + token + "; expires=Thu, 13 May 2099 12:00:00 UTC"
}
function setUserTokenCookie(token) {
    document.cookie = USER_TOKEN_COOKIE + "=" + token + "; expires=Thu, 13 May 2099 12:00:00 UTC"
}

function clearUserCookies() {
    clearCookie(USER_NAME_COOKIE)
    clearCookie(USER_ID_COOKIE)
    clearCookie(USER_TOKEN_COOKIE)

}

async function buildPostUserLoginRequest(baseUri, userName, password) {
    let uriLoginUser = baseUri + "/user-management/users/login"
    console.log("login user: " + uriLoginUser)

    return fetch(uriLoginUser, {
        method: "POST",
        mode: "cors",
        keepalive: false,
        headers: {"Authorization": await createBasicAuthValue(userName, password)},
    })
}

async function buildPostUserLogoutRequest(baseUri) {
    let uriLogoutUser = baseUri + "/user-management/users/logout"
    console.log("logout user: " + uriLogoutUser + " = " + getCookie(USER_ID_COOKIE))

    return fetch(uriLogoutUser, {
        method: "POST",
        mode: "cors",
        keepalive: false,
        headers: {"Authorization": createBearerAuthValue(getCookie(USER_TOKEN_COOKIE))},
    })
}

async function buildGetUserTokenRefreshRequest(baseUri, userName, password) {
    let uriLoginUser = baseUri + "/user-management/users/refresh-token"
    console.log("login user: " + uriLoginUser)

    return fetch(uriLoginUser, {
        method: "GET",
        mode: "cors",
        keepalive: false,
        headers: {"Authorization": createBearerAuthValue(getCookie(USER_TOKEN_COOKIE))},
    })
}

function buildGetUsersRequest(baseUri) {
    let uriGetUsers = baseUri + "/user-management/users"
    console.log("Fetching users: " + uriGetUsers)

    return fetch(uriGetUsers, {
        method: "GET",
        mode: "cors",
        keepalive: false,
        headers: {"Authorization": createBearerAuthValue(getCookie(USER_TOKEN_COOKIE))}
    })
}

/*
HEADERS
*/

async function createBasicAuthValue(userName, password) {
    let b64 = btoa(userName + ":" + (await digestMessage(password)))
    return "Basic " + b64
}

function createBearerAuthValue(token) {
    return "Bearer " + token
}

/*
COOKIES
 */

function clearCookie(cname) {
    document.cookie = cname + "=" + "; expires=Thu, 13 May 1970 12:00:00 UTC"
}

function getCookie(cname) {
    let name = cname + "="
    let decodedCookie = decodeURIComponent(document.cookie)
    let ca = decodedCookie.split(";")
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i]
        while (c.charAt(0) === " ") {
            c = c.substring(1)
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length)
        }
    }
    return ""
}

/*
HASH
 */
async function digestMessage(message) {
    const encoder = new TextEncoder();
    const data = encoder.encode(message);
    if (IS_SECURE_MODE) {
        let digest = await window.crypto.subtle.digest("SHA-256", data);
        return toHexString(new Uint8Array(digest))
        //return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))
    } else {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                resolve(SHA1(message));
            }, 300);
        })
    }
}

function getEpochSeconds() {
    return Math.round(new Date().getTime() / 1000)
}

function timestampToDate(utcSeconds) {
    let d = new Date(0); // The 0 there is the key, which sets the date to the epoch
    d.setUTCSeconds(utcSeconds)
    return d.toLocaleDateString() + " " + d.toLocaleTimeString()
}

function sayHi() {
    return "Hi! " + Date.now()
}

function getRandomInt(min = 0, max = 100) {
    return Math.floor((Math.random() * max + min) - min)
}


/** * *  Secure Hash Algorithm (SHA1) *  http://www.webtoolkit.info/
 *
 *source:  https://www.webtoolkit.info/javascript_sha1.html
 * **/
function toHexString(byteArray) {
    return Array.from(byteArray, function (byte) {
        return ('0' + (byte & 0xFF).toString(16)).slice(-2);
    }).join('')
}

function SHA1(msg) {
    function rotate_left(n, s) {
        var t4 = (n << s) | (n >>> (32 - s));
        return t4;
    };

    function lsb_hex(val) {
        var str = "";
        var i;
        var vh;
        var vl;
        for (i = 0; i <= 6; i += 2) {
            vh = (val >>> (i * 4 + 4)) & 0x0f;
            vl = (val >>> (i * 4)) & 0x0f;
            str += vh.toString(16) + vl.toString(16);
        }
        return str;
    };

    function cvt_hex(val) {
        var str = "";
        var i;
        var v;
        for (i = 7; i >= 0; i--) {
            v = (val >>> (i * 4)) & 0x0f;
            str += v.toString(16);
        }
        return str;
    };

    function Utf8Encode(string) {
        string = string.replace("/\r\n/g", "\n");
        var utftext = "";
        for (var n = 0; n < string.length; n++) {
            var c = string.charCodeAt(n);
            if (c < 128) {
                utftext += String.fromCharCode(c);
            } else if ((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);
            } else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);
            }
        }
        return utftext;
    };

    var blockstart;
    var i, j;
    var W = new Array(80);
    var H0 = 0x67452301;
    var H1 = 0xEFCDAB89;
    var H2 = 0x98BADCFE;
    var H3 = 0x10325476;
    var H4 = 0xC3D2E1F0;
    var A, B, C, D, E;
    var temp;
    msg = Utf8Encode(msg);
    var msg_len = msg.length;
    var word_array = new Array();
    for (i = 0; i < msg_len - 3; i += 4) {
        j = msg.charCodeAt(i) << 24 | msg.charCodeAt(i + 1) << 16 |
            msg.charCodeAt(i + 2) << 8 | msg.charCodeAt(i + 3);
        word_array.push(j);
    }
    switch (msg_len % 4) {
        case 0:
            i = 0x080000000;
            break;
        case 1:
            i = msg.charCodeAt(msg_len - 1) << 24 | 0x0800000;
            break;
        case 2:
            i = msg.charCodeAt(msg_len - 2) << 24 | msg.charCodeAt(msg_len - 1) << 16 | 0x08000;
            break;
        case 3:
            i = msg.charCodeAt(msg_len - 3) << 24 | msg.charCodeAt(msg_len - 2) << 16 | msg.charCodeAt(msg_len - 1) << 8 | 0x80;
            break;
    }
    word_array.push(i);
    while ((word_array.length % 16) != 14) word_array.push(0);
    word_array.push(msg_len >>> 29);
    word_array.push((msg_len << 3) & 0x0ffffffff);
    for (blockstart = 0; blockstart < word_array.length; blockstart += 16) {
        for (i = 0; i < 16; i++) W[i] = word_array[blockstart + i];
        for (i = 16; i <= 79; i++) W[i] = rotate_left(W[i - 3] ^ W[i - 8] ^ W[i - 14] ^ W[i - 16], 1);
        A = H0;
        B = H1;
        C = H2;
        D = H3;
        E = H4;
        for (i = 0; i <= 19; i++) {
            temp = (rotate_left(A, 5) + ((B & C) | (~B & D)) + E + W[i] + 0x5A827999) & 0x0ffffffff;
            E = D;
            D = C;
            C = rotate_left(B, 30);
            B = A;
            A = temp;
        }
        for (i = 20; i <= 39; i++) {
            temp = (rotate_left(A, 5) + (B ^ C ^ D) + E + W[i] + 0x6ED9EBA1) & 0x0ffffffff;
            E = D;
            D = C;
            C = rotate_left(B, 30);
            B = A;
            A = temp;
        }
        for (i = 40; i <= 59; i++) {
            temp = (rotate_left(A, 5) + ((B & C) | (B & D) | (C & D)) + E + W[i] + 0x8F1BBCDC) & 0x0ffffffff;
            E = D;
            D = C;
            C = rotate_left(B, 30);
            B = A;
            A = temp;
        }
        for (i = 60; i <= 79; i++) {
            temp = (rotate_left(A, 5) + (B ^ C ^ D) + E + W[i] + 0xCA62C1D6) & 0x0ffffffff;
            E = D;
            D = C;
            C = rotate_left(B, 30);
            B = A;
            A = temp;
        }
        H0 = (H0 + A) & 0x0ffffffff;
        H1 = (H1 + B) & 0x0ffffffff;
        H2 = (H2 + C) & 0x0ffffffff;
        H3 = (H3 + D) & 0x0ffffffff;
        H4 = (H4 + E) & 0x0ffffffff;
    }
    var temp = cvt_hex(H0) + cvt_hex(H1) + cvt_hex(H2) + cvt_hex(H3) + cvt_hex(H4);
    return temp.toLowerCase();
}

