# Workflow
- Scrape *disclosure of interest pdfs* from `SGX company announcements `
  - https://gist.github.com/neoyipeng2018/403acb271c14ee7dcd5dfbbe17bee2cc
- Parse pdf to get info e.g. [Form type](https://www.mas.gov.sg/regulation/capital-markets/disclosure-of-interest-in-listed-securities), Appointment and Name, Name of securities purchased, NUmber of securities purchased, Total value, etc...
- Add to db
- Display in terminal or webpage

# PDF Parsing
- [pypdf](https://pypdf.readthedocs.io/en/stable/)
- ???????

# Potential Issues
- Some pages on SGX may not have pdf and instead display all the info on the webpage
  - e.g. https://links.sgx.com/1.0.0/corporate-announcements/97995B9DFDBC6B5A48257A9500070A1F/9f6ada450634b807703668e074c93b413ee0bc19047ec60aa238ae62b661a712

https://stackoverflow.com/questions/3984003/how-to-extract-pdf-fields-from-a-filled-out-form-in-python
https://stackoverflow.com/questions/55754342/pdf2image-how-to-read-pdfs-with-enable-all-features-windows
https://stackoverflow.com/questions/68261052/pypdf-unable-to-read-xfa-pdf-file-after-it-has-been-filled-in-using-itextsharp