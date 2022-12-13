// For each key in lang, get the id from the document and set the text
// to the value of the key in lang
for (let key in lang) {
    try {
        document.getElementById(key).innerHTML = lang[key];
    } catch (error) {
        console.log(error);
    }
}
