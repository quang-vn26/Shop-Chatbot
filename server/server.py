# -*- coding: utf-8 -*-
import json
import requests
from pprint import pprint 
from bottle import debug, request, route, run
import random
from fuzzywuzzy import fuzz
import chatbot_response as cr

GRAPH_URL = "https://graph.facebook.com/v7.0"
PAGE_TOKEN = "EAAQgLn1gchgBALxAaZCzQ0sSUBLsRRaUUA5NT6pxEuU4bDfdkEZCOJm6meINy24ieDwxsk3wBH452vMrEU2DyHVAEI2oJC87Yp2Fjlsm9mzTb7lKu11cLZCwZCVoj9D9u6ZBZAtEq4XVLzHgGPvmt7vUJJqO4NYd1rUaHWAF2fa2SHfZCPDGJSt"
img_response_links = [
	"https://i.pinimg.com/originals/6e/24/db/6e24db7e8d4d98939d65081fc50259ca.jpg",
	"https://cdn.fbsbx.com/v/t59.2708-21/50209078_1964105090374772_5383357286351634432_n.gif?_nc_cat=1&_nc_sid=041f46&_nc_ohc=OYprwZ2EfS4AX-r6Sj-&_nc_ht=cdn.fbsbx.com&oh=dbf1809b8c5dc7d60cdbe525082c3b1a&oe=5EE0125A",
	"https://cdn.fbsbx.com/v/t59.2708-21/19148177_480572742299122_5902762623648137216_n.gif?_nc_cat=102&_nc_sid=041f46&_nc_ohc=hRxfAmKM6c8AX9M9xFD&_nc_ht=cdn.fbsbx.com&oh=833107ac77cde9d3aa9d934c3d75bef6&oe=5EE073C5",
	"https://cdn.fbsbx.com/v/t59.2708-21/20688801_1488190267930669_973320953134055424_n.gif?_nc_cat=110&_nc_sid=041f46&_nc_ohc=B_Ax8jJQCN8AX-RsOct&_nc_ht=cdn.fbsbx.com&oh=5738bace2a99f9a6dc2d76349b331088&oe=5EE08989", 
	"https://cdn.fbsbx.com/v/t59.2708-21/30860059_2065543057033056_3518753314181218304_n.gif?_nc_cat=103&_nc_sid=041f46&_nc_ohc=cLKdSKZhLosAX_Eruhk&_nc_ht=cdn.fbsbx.com&oh=9c0dc5c7b84201d656f83ca58a7ba1c7&oe=5EE07794"
]

with open("data/rat_20_05_2020.json", "r", encoding="utf-8") as json_data:
	rat = json.load(json_data)

with open("data/dishes_data.json", "r", encoding="utf-8") as json_data:
	database = json.load(json_data)

drink_topping = {}
for values in database.values():
	for value in values:
		drink_topping[value["name"]] = value["customs"]

status_code = -1
user_info = {}
user_info['drink'] = []
user_info['topping'] = []
user_info['total_cost'] = 0

def send_to_messenger(ctx):
	url = "{0}/me/messages?access_token={1}".format(GRAPH_URL, PAGE_TOKEN)
	response = requests.post(url, json=ctx)

def get_location(str):
	max_ratio = 0
	cand = None
	for hash_code, values in rat.items():
		for raw_address in values["raw_address"]:
			ratio = fuzz.token_sort_ratio(raw_address.lower(), str.lower())
			if ratio > max_ratio:
				max_ratio = ratio
				cand = values
				print(ratio)
				print(raw_address)
	if max_ratio > 70:
		return cand
	return None

def create_all_drink_elements():
	all_drink_list = []
	idx = 0
	for values in database.values():
		for value in values:
			a_dict = {}
			a_dict["title"] = value["name"]
			a_dict["image_url"] = value["image"]
			a_dict["subtitle"] = "{}; Gi??: {}??".format(value["description"], value["price"])
			a_dict["buttons"] = [
				{
					"type": "postback",
					"payload": "/order_drink_{}".format(value['id']),
					"title": "?????t h??ng"
				}
			]
			all_drink_list.append(a_dict)
			idx += 1
			if idx == 10:
				return all_drink_list
	return all_drink_list

def get_drink_value_by_payload(payload):
	for values in database.values():
		for value in values:
			if str(value['id']) == payload.split('_')[-1]:
				return value

def get_drink_value_by_name(name):
	for values in database.values():
		for value in values:
			if value['name'] == name:
				return value

def get_topping_value_by_drink_name_and_payload(drink_name, payload):
	topping_id = payload.split('_')[-1]
	value = get_drink_value_by_name(drink_name)
	for x in value["customs"][0]["customOptions"]:
		if str(x["id"]) == topping_id:
			return x


def create_all_topping_elements():
	all_topping_list = []
	idx = 0
	value = get_drink_value_by_name(user_info['drink'][-1])

	y = 0
	for x in value["customs"][0]["customOptions"]:
		a_dict = {}
		a_dict["title"] = x["value"]
		a_dict["subtitle"] = "Gi??: {}??".format(x["price"])
		a_dict["buttons"] = [
			{
				"type": "postback",
				"payload": "/order_topping_{}_{}".format(value['id'], x['id']),
				"title": "?????t h??ng"
			}
		]
		all_topping_list.append(a_dict)
		y += 1
		if y == 10:
			return all_topping_list
	return all_topping_list

@route("/webhook", method=["GET", "POST"])
def bot_endpoint():
	if request.method.lower() == "get":
		# verify_token = request.GET.get("hub.verify_token")
		# print(verify_token)
		hub_challenge = request.GET.get("hub.challenge")
		url = "{0}/me/subscribed_apps?access_token={1}".format(GRAPH_URL, PAGE_TOKEN)
		response = requests.post(url)
		return hub_challenge
	else:
		global status_code
		global user_info

		body = json.loads(request.body.read())
		user_id = body["entry"][0]["messaging"][0]["sender"]["id"]
		page_id = body["entry"][0]["id"]
		# pprint(body)
		ctx = {}
		if user_id != page_id:
			ctx["recipient"] = {"id":user_id}

		if "message" in body["entry"][0]["messaging"][0]:
			message = body["entry"][0]["messaging"][0]["message"]
			
			# sticker, image, gif
			if "attachments" in message:
				new_dict = {}
				new_dict["type"] = "image"
				random_link = random.choice(img_response_links)
				new_dict["payload"] = {"url":random_link}
				ctx["message"] = {"attachment":new_dict}
			# Regular text or icon
			elif "text" in message:
				text = message["text"]
				if status_code == -1:
					tag, _ = cr.classify(text)
					
					if tag != "ask_drink" and tag != "order" and tag != "coupon" and tag != "payment":
						ctx["message"] = {"text": cr.response(tag)}
					elif tag == "coupon":
						ctx["message"] = {"text": cr.response(tag)}
						# Will extend in the future
					elif tag == "payment":
						small_ctx = ctx.copy()
						small_ctx["message"] = {"text": cr.response(tag)}
						response = send_to_messenger(small_ctx)

						status_code = 0
						ctx["message"] = {"text": "S??? ??i???n tho???i c???a b???n l??: (V?? d???: 0902210496, +84902210496,...)"}
					else:
						small_ctx = ctx.copy()
						small_ctx["message"] = {"text": cr.response(tag)}
						response = send_to_messenger(small_ctx)

						new_dict = {}
						new_dict["type"] = "template"
						new_dict["payload"] = {"template_type":"generic", "elements":create_all_drink_elements()}
						ctx["message"] = {"attachment":new_dict}
				else:
					if status_code == 0:
						try:
							phone = message['nlp']['entities']['phone_number'][0]['value']
							user_info['phone'] = phone
							status_code += 1
							ctx["message"] = {"text": "OK M??nh ???? ghi nh???n s??? ??i???n tho???i c???a b???n. Ti???p theo cho m??nh xin th???i gian b???n mu???n nh???n ????? nh??. (V?? d???: 3 gi??? chi???u, 15:00,...)"}
						except KeyError:
							ctx["message"] = {"text": "M??nh kh??ng th??? nh???n ra s??? ??i???n tho???i c???a b???n. Nh???p l???i gi??p m??nh nh??"}
					elif status_code == 1:
						try:
							datetime = message['nlp']['entities']['datetime'][0]['value']
							user_info['datetime'] = datetime
							status_code += 1
							ctx["message"] = {"text": "M??nh ???? c?? th??ng tin v??? th???i gian b???n mu???n nh???n ?????. Cu???i c??ng cho m??nh xin ?????a ch??? nh??. (V?? d???: 295 B???ch Mai, Hai B?? Tr??ng, H?? N???i,...)"}
						except KeyError:
							ctx["message"] = {"text": "M??nh kh??ng bi???t b???n nh???p m???y gi??? lu??n. Cho m??nh xin l???i nh??!"}
					elif status_code == 2:
						# try:
						# location = message['nlp']['entities']['location'][0]['value']
						# Fuzzywuzzy
						location_value = get_location(text)
						if location_value != None:
							user_info['location'] = location_value
							if 'pid' in user_info['location']:
								del user_info['location']['pid']
							if 'raw_address' in user_info['location']:
								del user_info['location']['raw_address']

							location_str = ''
							for key, value in user_info['location'].items():
								location_str += ' - ' + key + ': ' + value + '\n'

							drink_str = ''
							for i, drink in enumerate(user_info['drink']):
								topping = user_info['topping'][i]
								if topping != None:
									drink_str += ' - 1 ' + drink + ' v???i topping ' + topping + '\n'
								else:
									drink_str += ' - 1 ' + drink + '\n'

							status_code += 1
							ctx["message"] = {
							"text": 'M??nh t???ng k???t l???i nh??:\n*????? u???ng:\n'
								'{}*S??? ??i???n tho???i: {}\n'
								'*Gi??? l???y ?????: {}\n'
								'*?????a ch??? b???n nh???p: {}\n'
								'*?????a ch??? chu???n h??a: \n{}\n'
								'*T???ng thi???t h???i v??? chi l??: {} nha.'
								.format(
									drink_str, 
									user_info['phone'], 
									user_info['datetime'], 
									text, 
									location_str, 
									user_info['total_cost']
									)
							}
						else:
							ctx["message"] = {"text": "?????a ch??? l??? qu?? b???n ??i, b?????c cu???i r???i c??? nh???p chu???n n??o."}
						# except KeyError:
						# 	ctx["message"] = {"text": "?????a ch??? b???n nh???p l??? qu??, m??nh kh??ng hi???u ???????c ??, nh???p l???i m???t l???n gi??m m??nh nha."}

					else:
						user_info = {}
						user_info['drink'] = []
						user_info['topping'] = []
						user_info['total_cost'] = 0
						ctx["message"] = {"text": "Phi v??? c?? c???a ch??ng ta xong r???i ????. Ch??ng ta l??m ????n h??ng m???i th??i nh???."}
						status_code = -1
		# postback
		elif "postback" in body["entry"][0]["messaging"][0]:
			payload = body["entry"][0]["messaging"][0]["postback"]["payload"]

			if payload.startswith("/order_drink"):
				value = get_drink_value_by_payload(payload)
				user_info['drink'].append(value["name"])
				user_info['total_cost'] += value["price"]

				ctx["message"] = {
					"attachment": {
						"type": "template",
						"payload": {
							"template_type": "generic",
							"elements": [
								{
									"title": "B???n c?? mu???n d??ng th??m topping kh??ng?",
									"buttons": [
										{
											"type": "postback",
											"payload": "/yes_topping",
											"title": "OK"
										},
									  {
											"type": "postback",
											"payload": "/no_topping",
											"title": "Kh??ng nha"
										},  
									]
								}
							]
						}
					}
				}
			elif payload.startswith("/no_topping"):
				user_info['topping'].append(None)
				ctx["message"] = {"text": "OK. B???n c?? th??? g???i th??m ????? kh??c ho???c h?? m??nh ki???u nh?? \"Cho m??nh thanh to??n c??i\" ????? thanh to??n nh??."}
			elif payload.startswith("/yes_topping"):
				small_ctx = ctx.copy()
				small_ctx["message"] = {"text": "M???i ch???n topping ???:"}
				response = send_to_messenger(small_ctx)
				new_dict = {}
				new_dict["type"] = "template"
				new_dict["payload"] = {"template_type":"generic", "elements":create_all_topping_elements()}
				ctx["message"] = {"attachment":new_dict}
			elif payload.startswith("/order_topping"):
				value = get_topping_value_by_drink_name_and_payload(user_info['drink'][-1], payload)
				user_info['topping'].append(value["value"])
				user_info['total_cost'] += value["price"]
				ctx["message"] = {"text": "L???a ch???n tuy???t v???i ?????y. Gi??? b???n c?? th??? n??i chuy???n ti???p v???i m??nh, ho???c mua ????? m???i ho???c l??c n??o mu???n t??nh ti???n th?? c?? th??? k??u m??nh ki???u nh?? \"T??nh ti???n cho m??nh v???i\" ????? m??nh ch???t ????n nh??"}
		# print("================================")
		# pprint(ctx)
		response = send_to_messenger(ctx)
		return ""


debug(True)
run(reloader=True, port=8088)
