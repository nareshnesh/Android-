# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo import SUPERUSER_ID

dbname = ''
author_id = ''
author_name = ''


class AutoPushChatNotification(models.TransientModel):
    _name = "auto.push.chat.notification"
    _description = "Auto Push Chat Notifications"

    def notify(self, notify_users=False, model_name=False, record_id=False, subject='Chat Notification', content='To View Record ', link_name="click here", action_id=False):
        if self.env.user.push_notification:
            dbname = self.env.cr.dbname
            author_id = self.env.user.partner_id.id or False
            author_name = self.env.user.partner_id.name or ''
            ch_obj = self.env['mail.channel']
            
            if notify_users and model_name and record_id:
                body = '<p>'
                if action_id:
                    body = body + content + ' : <a href="#id='+str(record_id)+'&view_type=form&model='+ model_name + '&action='+str(action_id)+'"' + ' target="_blank">'+str(link_name)+'</a>'
                else:    
                    body = body + content + ' : <a href="#id='+str(record_id)+'&view_type=form&model='+ model_name +'"' + ' target="_blank">'+str(link_name)+'</a>'
                body = body + '</p>'
                for user in notify_users:
                    if user.id != self.env.user.id:
#                     if user.id != self.env.user.id and user.receive_notification:
                        sql="select id,name,email from res_partner where name= '"+user.name+"' limit 1"
                        self.env.cr.execute(sql)
                        reslt = self.env.cr.fetchall()
                        for res in reslt:
                            try:
                                ch_name = res[1]+', '+self.env.user.name
                                channel_id = ch_obj.search([('name', 'ilike', str(ch_name))])
                                channel_partner_to_add = [(4, self.env.user.partner_id.id),(4, res[0])] ## we have to add opposite users related oartner_id
                                if not channel_id:
                                    channel_id = ch_obj.search([('name', 'ilike', str(self.env.user.name+', '+res[1]))])
                                    if not channel_id:        
                                        vals = {
                                                'channel_partner_ids': channel_partner_to_add,
                                                'channel_type': 'chat',
                                                'name': ch_name,
                                                'public': 'private',
                                                'email_send': False,
                                            }
                                        channel_id = ch_obj.create(vals)
                                        sql = """update mail_channel_partner set is_pinned=True where channel_id = %s"""%(channel_id.id)
                                        self.env.cr.execute(sql)                                        
                                if channel_id:
                                    notification = self.create_notification(subject, body, self.env.user, ch_name, channel_id.id, res)
                                    self.env['bus.bus'].sendmany(notification)
                            except Exception as e:
                                pass ## to avoid exception and continue the flow
        
        return True
    
    @api.multi
    def create_notification(self, subject, body, user_ids, ch_name, ch_id, res):
        user_email = ''
        if user_ids.partner_id.email:
            user_email = user_ids.partner_id.email 
        message_id = self.env['mail.message'].create({
                                                'subject': _('%s') % (subject),
                                                'body': body,
                                                'subtype_id': 1,
                                                'record_name': ch_name,
                                                'email_from': user_ids.name + " <"+user_email+">",
                                                'reply_to': user_ids.name + " <"+user_email +">",
                                                'model': 'mail.channel',
                                                'res_id': ch_id,
                                                'message_type': 'comment',
                                                'no_auto_thread': False,
                                            })
        name_rec = res[1]+", "+user_ids.name
        date = str(datetime.now())[:19]
        email_from = res[1]+' <'+res[2]+'>'
        notification = [[(dbname, 'mail.channel', ch_id),         {
            'body': body, 'body_short': False, 'record_name': name_rec, 'tracking_value_ids': [], 
            'channel_ids': [ch_id], 'subtype_description': False, 'date': date, 'partner_ids': [], 'author_id': (author_id, author_name), 
            'subject': False, 'attachment_ids': [], 'needaction_partner_ids': [], 'message_type': u'comment', 'starred_partner_ids': [], 
            'id': message_id.id, 'is_note': False, 'subtype_id': (1, u'Discussions'), 'model': u'mail.channel', 'res_id': ch_id, 
            'email_from': email_from        }    ]]
                                    
        return notification

