import uiScriptLocale
import app

ROOT = "d:/ymir work/ui/game/"

Y_ADD_POSITION = 0
window = {
	"name" : "ExpandTaskBar",
	"style" : ("ltr", ),

	"x" : SCREEN_WIDTH/2 - 5,
	"y" : SCREEN_HEIGHT - 74,

	"width" : 37,
	"height" : 37,

	"children" :
	[
		{
			"name" : "ExpanedTaskBar_Board",
			"type" : "window",
			"style" : ("ltr", ),

			"x" : 0,
			"y" : 0,

			"width" : 37,
			"height" : 37,

			"children" :
			[
				{
					"name" : "DragonSoulButton",
					"type" : "button",
					"style" : ("ltr", ),

					"x" : 0,
					"y" : 0,

					"width" : 37,
					"height" : 37,

					"tooltip_text" : uiScriptLocale.TASKBAR_DRAGON_SOUL,
							
					"default_image" : "d:/ymir work/ui/dragonsoul/DragonSoul_Button_01.tga",
					"over_image" : "d:/ymir work/ui/dragonsoul/DragonSoul_Button_02.tga",
					"down_image" : "d:/ymir work/ui/dragonsoul/DragonSoul_Button_03.tga",
				},
			],
		},		
	],
}

window["width"] = 37*2
window["children"][0]["width"] = window["children"][0]["width"] + 37
window["children"][0]["children"] = window["children"][0]["children"] + [
				{
					"name" : "AutoButton",
					"type" : "button",
					"style" : ("ltr", ),

					"x" : 38,
					"y" : 0,

					"width" : 37,
					"height" : 37,

					"tooltip_text" : uiScriptLocale.KEYCHANGE_AUTO_WINDOW,
							
					"default_image" : "icon/item/TaskBar_Auto_Button_01.tga",
					"over_image" : "icon/item/TaskBar_Auto_Button_02.tga",
					"down_image" : "icon/item/TaskBar_Auto_Button_03.tga",
				},]


window["width"] = 37*3
window["children"][0]["width"] = window["children"][0]["width"] + 37
window["children"][0]["children"] = window["children"][0]["children"] + [
				{
					"name" : "PetInfoButton",
					"type" : "button",
					"style" : ("ltr", ),

					"x" : 74,
					"y" : 0,

					"width" : 37,
					"height" : 37,

					"tooltip_text" : "fdsafsd",
							
					"default_image" : "d:/ymir work/ui/pet/TaskBar_Pet_Button_01.tga",
					"over_image" : "d:/ymir work/ui/pet/TaskBar_Pet_Button_02.tga",
					"down_image" : "d:/ymir work/ui/pet/TaskBar_Pet_Button_03.tga",
				},]
				
window["width"] = 37*4
window["children"][0]["width"] = window["children"][0]["width"] + 37
window["children"][0]["children"] = window["children"][0]["children"] + [
				{
					"name" : "MonsterCardWindow",
					"type" : "button",
					"style" : ("ltr", ),

					"x" : 110,
					"y" : 0,

					"width" : 37,
					"height" : 37,

					"tooltip_text" : uiScriptLocale.KEYCHANGE_MONSTER_CARD_WINDOW,
							
					"default_image" : "icon/item/Mcard_Button_01.tga",
					"over_image" : "icon/item/Mcard_Button_02.tga",
					"down_image" : "icon/item/Mcard_Button_03.tga",
				},]
				
window["width"] = 37*5
window["children"][0]["width"] = window["children"][0]["width"] + 37
window["children"][0]["children"] = window["children"][0]["children"] + [
				{
					"name" : "PartyMatchButton",
					"type" : "button",
					"style" : ("ltr", ),

					"x" : 146,
					"y" : 0,

					"width" : 37,
					"height" : 37,

					"tooltip_text" : uiScriptLocale.KEYCHANGE_PARTY_MATCH_WINDOW,
							
					"default_image" : "icon/item/party_button_01.tga",
					"over_image" : "icon/item/party_button_02.tga",
					"down_image" : "icon/item/party_button_03.tga",
				},]

if app.ENABLE_DRAGON_GATE:
	window["width"] = 37 * 6
	window["children"][0]["width"] = window["children"][0]["width"] + 37
	window["children"][0]["children"] = window["children"][0]["children"] + [
	{
		"name" : "DragonGateButton",
		"type" : "button",
		"style" : ("ltr", ),

		"x" : 182,
		"y" : 0,

		"width" : 37,
		"height" : 37,

		"tooltip_text" : uiScriptLocale.KEYCHANGE_DRAGON_GATE,
				
		"default_image" : "icon/item/dragondoor_01.tga",
		"over_image" : "icon/item/dragondoor_02.tga",
		"down_image" : "icon/item/dragondoor_03.tga",
	},]

if app.ENABLE_MERCENARY_SYSTEM:
	window["width"] = 37 * 7
	window["children"][0]["width"] = window["children"][0]["width"] + 37
	window["children"][0]["children"] = window["children"][0]["children"] + [
	{
		"name" : "MercenaryButton",
		"type" : "button",
		"style" : ("ltr", ),

		"x" : 218,
		"y" : 0,

		"width" : 37,
		"height" : 37,

		"tooltip_text" : uiScriptLocale.KEYCHANGE_MERCENARY,
				
		"default_image" : "icon/item/mercenary_01.tga",
		"over_image" : "icon/item/mercenary_02.tga",
		"down_image" : "icon/item/mercenary_03.tga",
	},]

if app.ENABLE_SUNGMAHEE_GATE:
	window["width"] = 37 * 8
	window["children"][0]["width"] = window["children"][0]["width"] + 37
	window["children"][0]["children"] = window["children"][0]["children"] + [
	{
		"name" : "SungmaheeGateAchievButton",
		"type" : "button",
		"style" : ("ltr", ),

		"x" : 254,
		"y" : 0,

		"width" : 37,
		"height" : 37,

		"tooltip_text" : uiScriptLocale.KEYCHANGE_SUNGMAHEE_GATE_ACHIEV,
				
		"default_image" : "icon/item/smhgate_01.tga",
		"over_image" : "icon/item/smhgate_02.tga",
		"down_image" : "icon/item/smhgate_03.tga",
	},]