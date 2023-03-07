const report = require("multiple-cucumber-html-reporter");

report.generate({
  jsonDir: "./cucumber_results/",
  reportPath: "./cucumber_html/",
  metadata: {
    browser: {
      name: "N/A",
      version: "N/A",
    },
    device: "CircleCI",
    platform: {
      name: "N/A",
      version: "N/A",
    },
  },
  customData: {
    title: "Routing BDD",
    data: [],
  },
});
