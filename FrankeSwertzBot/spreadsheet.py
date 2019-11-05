import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import locale


class FrankeSwertzSheet():
    def __init__(self):
        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        client = gspread.authorize(creds)

        # Find a workbook by name and open the first sheet
        # Make sure you use the right name here.
        client = client.open("FrankeSwertzGroupMeetingSchedule")
        sheet = client.get_worksheet(0)
        self.all_sheet_data =  sheet.get_all_records()

    def get_next_meeting(self):
        today = datetime.today()
        for row in self.all_sheet_data:

            date = ' '.join(row['Date'].split('\xa0')[1:])
            locale.setlocale(locale.LC_TIME, "nl_NL")  # swedish
            try:
                datetime_object = datetime.strptime(date, '%d %b. %Y')
            except:
                datetime_object = datetime.strptime(date, '%d %b %Y')
            if(datetime_object < today):
                continue

            type = row['Type']
            presenter1 = row['Presenter 1']
            presenter2 = row['Presenter 2']
            location = row['Location']
            remark = row['Remark']
            # assume here that the rows are ordered, so the first entry that is not before today is the next meeting
            locale.setlocale(locale.LC_TIME, "en_GB")  # swedish
            message = ['Next FrankeSwertz meeting: '+datetime_object.strftime("%A %d %B %Y")]
            if len(presenter1) > 0:
                if len(presenter2) > 0:
                    message.append('Presenter 1: '+presenter1)
                else:
                    message.append('Presenter: ' + presenter1)
            if len(presenter2) > 0:
                message.append('Presenter 2: '+presenter2)
            message.append('Location: '+location)
            if len(remark) > 0:
                message.append('Remark: '+remark)
            return('\n'.join(message))

