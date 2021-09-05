$(function () {
    var images = ['RfxtJQzHuL8zWRLM1v/giphy.gif',
        '9mIstJHAZOPdnjLipw/giphy.gif',
        '6gifeytYL9tW947npk/giphy.gif',
        'PHulSKSYhYmTQU7Kjr/giphy.gif',
        'KZr3ZCv5xGelfLx4sL/giphy.gif',
        'Wevi91ylp5w9mbsVWE/giphy.gif',
        'fgBOraV0BRNxUsJBjK/giphy.gif',
        'rnLbMa0VPreDZzW6ES/giphy.gif',
        'f3fYD8jlO5pDelMgjZ/giphy.gif',
        'sni4RQv5Z1QYOIb3kA/giphy.gif'];
    $('body').css({ 'background-image': 'url(https://media.giphy.com/media/' + images[Math.floor(Math.random() * images.length)] + ')' });
});