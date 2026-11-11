// Stato company details. Fill each gap on ONE line when approved.
window.COMPANY = {
  name: "Stato Technologies Limited",
  companyNumber: "17541466", // fill when Companies House approves (submission 119-878150)
  icoNumber: "ZC285237",
  registeredOffice: "Regent House, Heaton Lane, Stockport SK4 1BS",
  email: "hello@stato.tech"
};
(function(){var C=window.COMPANY;function f(){document.querySelectorAll('[data-company]').forEach(function(el){var k=el.getAttribute('data-company');if(C[k])el.textContent=C[k];});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',f);else f();})();
