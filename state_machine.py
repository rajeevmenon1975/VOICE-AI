import time
import mock_apis
import database

# Dictionary containing beautiful templates in English, Hindi, and Gujarati
TEMPLATES = {
    "English": {
        "greeting": "Hello! This is the Research Desk at StoxBox. May I speak with {name}?",
        "disclaimer": "Before we begin, please note: stock market investments are subject to market risks. Please read all scheme documents carefully before trading.",
        "opt_in_prompt": "Would you like to hear our equity research recommendation for today?",
        "busy_exit": "No problem at all. I will call you at a more convenient time. Have a great day!",
        "pitch": "Our research desk has a strong BUY recommendation on {symbol} at the current market price of ₹{price:,.2f}. The target price is ₹{target:,.2f} with a stop loss of ₹{sl:,.2f}. Would you like to buy {qty} shares?",
        "rms_checking": "Checking your ledger margin and risk parameters in the background...",
        "rms_approved": "Great news! Your available ledger balance is ₹{balance:,.2f}, which is sufficient to meet our margin requirement of ₹{required:,.2f}.",
        "rms_insufficient": "Sir, this trade requires a margin of ₹{required:,.2f}, but your available balance is ₹{balance:,.2f}. We can place a smaller order for {new_qty} shares instead, or I can text you a UPI deposit link. Which would you prefer?",
        "sending_otp": "To authorize this trade securely, I have sent a 4-digit code to your registered mobile number. Please speak the 4-digit code now.",
        "otp_invalid": "That code doesn't match. Let's try again. Please speak the 4-digit verification code sent to your mobile phone.",
        "otp_blocked": "Security block: Too many incorrect OTP attempts. We cannot place this trade. Please contact our support desk.",
        "order_readback": "Perfect. Confirming a {action} order for {qty} shares of {symbol} on exchange {exchange} at {order_type} price using product {product}. Do you confirm this order? Please say 'Yes, I confirm' or 'Cancel'.",
        "trade_placed": "Excellent. Your order has been placed successfully. Order ID is {order_id}. I will call you back in a moment with the execution details once the trade settles. Thank you!",
        "order_cancelled": "No problem. I have cancelled the transaction. No trade was placed. Have a wonderful day!",
        "callback_greeting": "Hello {name}, this is a post-trade confirmation callback from [Broker Name].",
        "callback_executed": "Your {action} order of {qty} shares of {symbol} has been successfully executed at an average price of ₹{avg_price:,.2f}. Your updated ledger balance is ₹{balance:,.2f}. Thank you for trading with us!"
    },
    "Hindi": {
        "greeting": "नमस्ते! मैं स्टॉक्सबॉक्स रिसर्च डेस्क से बात कर रहा हूँ। क्या मेरी बात {name} जी से हो रही है?",
        "disclaimer": "शुरू करने से पहले कृपया ध्यान दें: शेयर बाजार में निवेश बाजार के जोखिमों के अधीन है। ट्रेडिंग करने से पहले सभी संबंधित दस्तावेजों को ध्यान से पढ़ें।",
        "opt_in_prompt": "क्या आप आज की हमारी इक्विटी रिसर्च सलाह सुनना चाहेंगे?",
        "busy_exit": "कोई बात नहीं। मैं आपको बाद में संपर्क करूँगा। आपका दिन शुभ हो!",
        "pitch": "हमारे रिसर्च डेस्क ने ₹{price:,.2f} के बाजार भाव पर {symbol} में BUY की सलाह दी है। इसका लक्ष्य ₹{target:,.2f} और स्टॉप लॉस ₹{sl:,.2f} है। क्या आप {qty} शेयर्स खरीदना चाहेंगे?",
        "rms_checking": "बैकग्राउंड में आपके लेजर मार्जिन और रिस्क मानकों की जांच की जा रही है...",
        "rms_approved": "अच्छी खबर है! आपका उपलब्ध लेजर बैलेंस ₹{balance:,.2f} है, जो आवश्यक मार्जिन ₹{required:,.2f} के लिए पर्याप्त है।",
        "rms_insufficient": "सर, इस ट्रेड के लिए ₹{required:,.2f} मार्जिन की आवश्यकता है, लेकिन आपका बैलेंस ₹{balance:,.2f} है। हम इसके बजाय {new_qty} शेयर्स का छोटा ऑर्डर दे सकते हैं, या मैं आपको एक UPI पेमेंट लिंक भेज सकता हूँ। आप क्या पसंद करेंगे?",
        "sending_otp": "इस ट्रेड को सुरक्षित रूप से अधिकृत करने के लिए, मैंने आपके रजिस्टर्ड मोबाइल नंबर पर 4 अंकों का कोड भेजा है। कृपया वह कोड बताएं।",
        "otp_invalid": "यह कोड सही नहीं है। कृपया फिर से प्रयास करें और 4 अंकों का कोड बताएं।",
        "otp_blocked": "सुरक्षा ब्लॉक: बहुत सारे गलत कोड दर्ज किए गए हैं। हम यह ट्रेड नहीं रख सकते। कृपया हमारे कस्टमर डेस्क से संपर्क करें।",
        "order_readback": "बहुत बढ़िया। {exchange} एक्सचेंज पर {symbol} के {qty} शेयर्स का {action} ऑर्डर, {product} प्रोडक्ट के तहत {order_type} भाव पर लगाने की पुष्टि करें। क्या आप इस ऑर्डर को कन्फर्म करते हैं? कृपया 'हाँ, कन्फर्म है' या 'कैंसिल' कहें।",
        "trade_placed": "बधाई हो! आपका ऑर्डर सफलतापूर्वक रख दिया गया है। ऑर्डर आईडी {order_id} है। जैसे ही ट्रेड पूरा होगा, मैं कुछ ही क्षणों में डिटेल्स के साथ आपको वापस कॉल करूँगा। धन्यवाद!",
        "order_cancelled": "ठीक है, मैंने इस ऑर्डर को रद्द कर दिया है। कोई ट्रेड नहीं किया गया। आपका दिन शुभ हो!",
        "callback_greeting": "नमस्ते {name} जी, यह [Broker Name] से आपकी ट्रेड कन्फर्मेशन कॉल है।",
        "callback_executed": "{symbol} के {qty} शेयर्स का आपका {action} ऑर्डर ₹{avg_price:,.2f} के औसत भाव पर सफलतापूर्वक एग्जीक्यूट हो गया है। आपका नया लेजर बैलेंस ₹{balance:,.2f} है। हमारे साथ ट्रेड करने के लिए धन्यवाद!"
    },
    "Gujarati": {
        "greeting": "નમસ્તે! હું [Broker Name] રિસર્ચ ડેસ્ક પરથી વાત કરી રહ્યો છું. શું હું {name} ભાઈ સાથે વાત કરી શકું?",
        "disclaimer": "શરૂ કરતા પહેલાં કૃપા કરીને નોંધ લો: શેરબજારમાં રોકાણ બજારના જોખમોને આધીન છે. ટ્રેડિંગ કરતા પહેલાં બધા દસ્તાવેજો ધ્યાનથી વાંચો.",
        "opt_in_prompt": "શું તમે આજે અમારી ઇક્વિટી રિસર્ચ ભલામણ સાંભળવા માંગો છો?",
        "busy_exit": "કોઈ વાંધો નહીં. હું તમને અનુકૂળ સમયે ફરીથી ફોન કરીશ. તમારો દિવસ સારો રહે!",
        "pitch": "અમારા રિસર્ચ ડેસ્કે ₹{price:,.2f} ના માર્કેટ ભાવ પર {symbol} ખરીદવાની (BUY) સલાહ આપી છે. લક્ષ્ય ₹{target:,.2f} અને સ્ટોપ લોસ ₹{sl:,.2f} છે. શું તમે {qty} શેર્સ ખરીદવા માંગો છો?",
        "rms_checking": "બેકગ્રાઉન્ડમાં તમારા લેજર બેલેન્સ અને રિસ્ક પેરામીટર્સની ચકાસણી થઈ રહી છે...",
        "rms_approved": "ખૂબ જ સરસ! તમારું ઉપલબ્ધ લેજર બેલેન્સ ₹{balance:,.2f} છે, જે જરૂરી માર્જિન ₹{required:,.2f} માટે પૂરતું છે.",
        "rms_insufficient": "સર, આ ટ્રેડ માટે ₹{required:,.2f} માર્જિનની જરૂર છે, પરંતુ તમારું બેલેન્સ ₹{balance:,.2f} છે. આપણે તેના બદલે {new_qty} શેર્સનો નાનો ઓર્ડર મૂકી શકીએ, અથવા હું તમને UPI પેમેન્ટ લિંક મોકલી આપું. તમે શું પસંદ કરશો?",
        "sending_otp": "આ ટ્રેડને સુરક્ષિત રીતે ઓથોરાઇઝ કરવા માટે, મેં તમારા રજિસ્ટર્ડ મોબાઈલ નંબર પર 4 અંકનો કોડ મોકલ્યો છે. કૃપા કરીને તે કોડ અત્યારે બોલો.",
        "otp_invalid": "કોડ ખોટો છે. કૃપા કરીને ફરીથી પ્રયત્ન કરો અને 4 અંકનો કોડ બોલો.",
        "otp_blocked": "સુરક્ષા બ્લોક: ખોટા કોડના ઘણા પ્રયાસો થયા છે. આ ટ્રેડ મૂકી શકાશે નહીં. કૃપા કરીને સપોર્ટ સેન્ટરનો સંપર્ક કરો.",
        "order_readback": "ઉત્તમ. {exchange} એક્સચેન્જ પર {symbol} ના {qty} શેર્સ માટેનો {action} ઓર્ડર, {product} પ્રોડક્ટ હેઠળ {order_type} ભાવ પર મુકવા માટે કન્ફર્મ કરો. શું તમે આ ઓર્ડર કન્ફર્મ કરો છો? કૃપા કરીને 'હા, કન્ફર્મ છે' અથવા 'કેન્સલ' બોલો.",
        "trade_placed": "અભિનંદન! તમારો ઓર્ડર સફળતાપૂર્વક મૂકી દેવામાં આવ્યો છે. ઓર્ડર આઈડી {order_id} છે. ઓર્ડર એક્ઝિક્યુટ થતાં જ હું વિગતો આપવા માટે ટૂંક સમયમાં તમને સામેથી ફોન કરું છું. આભાર!",
        "order_cancelled": "કોઈ વાંધો નહીં. મેં ઓર્ડર રદ કર્યો છે. કોઈ ટ્રેડ મૂકવામાં આવ્યો નથી. તમારો દિવસ શુભ રહે!",
        "callback_greeting": "નમસ્તે {name} ભાઈ, આ [Broker Name] તરફથી તમારા ટ્રેડ કન્ફર્મેશન માટેનો કોલ છે.",
        "callback_executed": "{symbol} ના {qty} શેર્સ માટેનો તમારો {action} ઓર્ડર ₹{avg_price:,.2f} ના સરેરાશ ભાવ પર સફળતાપૂર્વક એક્ઝિક્યુટ થઈ ગયો છે. તમારું અપડેટેડ લેજર બેલેન્સ ₹{balance:,.2f} છે. અમારી સાથે ટ્રેડ કરવા બદલ આભાર!"
    }
}

class VoiceAIStateMachine:
    def __init__(self, client_id: str, symbol: str, target: float, sl: float, recommended_qty: int):
        self.client_id = client_id
        self.symbol = symbol.upper()
        self.target = target
        self.sl = sl
        self.recommended_qty = recommended_qty
        
        # Load client profile and language
        self.client = database.get_client(client_id)
        if not self.client:
            raise ValueError(f"Client {client_id} not found in database.")
        
        self.lang = self.client["preferred_lang"]
        if self.lang not in TEMPLATES:
            self.lang = "English" # Default fallback
            
        self.stock = database.get_stock(self.symbol)
        if not self.stock:
            raise ValueError(f"Stock {self.symbol} is invalid.")

        # State Variables
        self.state = "INIT"
        self.call_id = f"CALL-{int(time.time())}"
        self.transcript_history = []
        self.order_qty = recommended_qty
        self.order_product = "CNC" # Default to Delivery (CNC) for long-term calls
        self.otp_retries = 0
        self.otp_code = None
        self.placed_order_details = None

    def speak(self, key: str, **kwargs) -> str:
        """Helper to fetch and format localized messages from templates."""
        text = TEMPLATES[self.lang][key].format(**kwargs)
        # Log AI speaker turn
        self.transcript_history.append(f"AI: {text}")
        return text

    def handle_input(self, user_speech: str) -> str:
        """
        State transitions driving the conversation.
        Processes transcribed user speech and returns the AI's audio response.
        """
        self.transcript_history.append(f"USER: {user_speech}")
        user_speech_clean = user_speech.strip().lower()

        # State 1: Greeting opt-in response
        if self.state == "INIT":
            # Greet first
            self.state = "GREETED"
            greeting_str = self.speak("greeting", name=self.client["name"])
            disclaimer_str = self.speak("disclaimer")
            opt_in_str = self.speak("opt_in_prompt")
            return f"{greeting_str}\n{disclaimer_str}\n{opt_in_str}"

        elif self.state == "GREETED":
            # Evaluate if client wants to hear research
            affirmative_words = ["yes", "ok", "sure", "haan", "ha", "bol", "boliye", "interest", "suno"]
            if any(word in user_speech_clean for word in affirmative_words):
                self.state = "PITCHED"
                return self.speak("pitch", symbol=self.symbol, price=self.stock["current_price"], target=self.target, sl=self.sl, qty=self.order_qty)
            else:
                self.state = "TERMINATED"
                return self.speak("busy_exit")

        # State 2: Pitch acceptance & margin check
        elif self.state == "PITCHED":
            affirmative_words = ["yes", "buy", "place", "shares", "kharido", "lai lo", "ha", "haan"]
            negative_words = ["no", "stop", "cancel", "nathi", "nako", "nahi"]
            
            if any(word in user_speech_clean for word in negative_words):
                self.state = "TERMINATED"
                return self.speak("order_cancelled")
                
            if any(word in user_speech_clean for word in affirmative_words):
                # Transitioning to RMS Pre-Check
                self.state = "RMS_CHECK"
                rms_status = mock_apis.validate_rms_rules(
                    client_id=self.client_id,
                    symbol=self.symbol,
                    transaction_type="BUY",
                    quantity=self.order_qty,
                    price_type="MARKET",
                    price=0.0,
                    product_type=self.order_product
                )

                if rms_status["status"] == "APPROVED":
                    self.state = "OTP_WAIT"
                    self.otp_code = mock_apis.send_voice_otp(self.client_id)
                    approved_str = self.speak("rms_approved", balance=self.client["ledger_balance"], required=rms_status["margin_required"])
                    otp_str = self.speak("sending_otp")
                    return f"{approved_str}\n{otp_str}"
                else:
                    # Check if shortfall can be adjusted by lowering quantity
                    margin_per_share = rms_status["margin_required"] / self.order_qty
                    available_funds = self.client["ledger_balance"]
                    adjustable_qty = int(available_funds // margin_per_share)
                    
                    if adjustable_qty >= 1:
                        self.state = "RMS_INSUFFICIENT_ADJUST"
                        # Propose alternative quantity
                        return self.speak("rms_insufficient", required=rms_status["margin_required"], balance=available_funds, new_qty=adjustable_qty)
                    else:
                        self.state = "TERMINATED"
                        return f"{rms_status['reason']}\n" + self.speak("order_cancelled")
            else:
                # Clarification prompt
                return "Sir, would you like to place this BUY order? Please say 'Yes' to proceed or 'No' to cancel."

        # State 2.1: Insufficient Margin Choice
        elif self.state == "RMS_INSUFFICIENT_ADJUST":
            # User decides to buy a smaller quantity or deposit funds
            decrease_qty_words = ["smaller", "less", "lower", "kam", "ochi", "ocho", "2", "yes", "shares", "chota", "adju"]
            if any(word in user_speech_clean for word in decrease_qty_words):
                # Calculate adjusted quantity
                rms_status = mock_apis.validate_rms_rules(
                    client_id=self.client_id,
                    symbol=self.symbol,
                    transaction_type="BUY",
                    quantity=self.order_qty,
                    price_type="MARKET",
                    price=0.0,
                    product_type=self.order_product
                )
                margin_per_share = rms_status["margin_required"] / self.order_qty
                self.order_qty = int(self.client["ledger_balance"] // margin_per_share)
                
                # Resend OTP
                self.state = "OTP_WAIT"
                self.otp_code = mock_apis.send_voice_otp(self.client_id)
                return self.speak("sending_otp")
            else:
                self.state = "TERMINATED"
                return self.speak("order_cancelled")

        # State 3: OTP Verification
        elif self.state == "OTP_WAIT":
            # Extract numbers from speech transcript
            spoken_digits = "".join(filter(str.isdigit, user_speech_clean))
            
            if mock_apis.verify_voice_otp(self.client_id, spoken_digits):
                self.state = "CONFIRM_WAIT"
                # Perform Readback (6-Parameter Rule compliance)
                return self.speak("order_readback", 
                                  action="BUY", 
                                  qty=self.order_qty, 
                                  symbol=self.symbol, 
                                  exchange="NSE", 
                                  order_type="MARKET", 
                                  product=self.order_product)
            else:
                self.otp_retries += 1
                if self.otp_retries >= 3:
                    self.state = "TERMINATED"
                    return self.speak("otp_blocked")
                return self.speak("otp_invalid")

        # State 4: Final Order Placement Confirmation
        elif self.state == "CONFIRM_WAIT":
            confirm_words = ["yes", "confirm", "place", "haan", "ha", "manzoor", "thik chhe", "kari do"]
            if any(word in user_speech_clean for word in confirm_words):
                # Execute Trade through OMS
                recording_url = f"https://recordings.broker.com/voice-records/{self.call_id}.mp3"
                oms_result = mock_apis.place_order(
                    client_id=self.client_id,
                    symbol=self.symbol,
                    transaction_type="BUY",
                    quantity=self.order_qty,
                    price_type="MARKET",
                    price=0.0,
                    product_type=self.order_product,
                    recording_url=recording_url
                )

                if oms_result["status"] == "success":
                    self.state = "COMPLETED"
                    self.placed_order_details = oms_result["data"]
                    # Log call record in DB before finishing
                    database.log_call(
                        call_id=self.call_id,
                        client_id=self.client_id,
                        phone=self.client["phone"],
                        call_type="OUTBOUND_PITCH",
                        recording_url=recording_url,
                        transcript="\n".join(self.transcript_history)
                    )
                    return self.speak("trade_placed", order_id=oms_result["data"]["order_id"])
                else:
                    self.state = "TERMINATED"
                    return f"OMS Error: {oms_result['message']}. " + self.speak("order_cancelled")
            else:
                self.state = "TERMINATED"
                return self.speak("order_cancelled")

        return "Goodbye."

    def execute_callback_call(self) -> str:
        """Simulates the outbound Callback confirming full trade execution."""
        if not self.placed_order_details:
            return "No completed order found to execute callback."

        callback_call_id = f"CALL-CB-{int(time.time())}"
        recording_url = f"https://recordings.broker.com/voice-records/{callback_call_id}.mp3"
        
        # Load updated client data to read correct balance
        updated_client = database.get_client(self.client_id)
        
        # Build transcripts
        greet = TEMPLATES[self.lang]["callback_greeting"].format(name=self.client["name"])
        details = TEMPLATES[self.lang]["callback_executed"].format(
            action="BUY",
            qty=self.order_qty,
            symbol=self.symbol,
            avg_price=self.placed_order_details["average_price"],
            balance=updated_client["ledger_balance"]
        )
        
        full_callback_script = f"{greet}\n{details}"
        
        # Log Callback call to compliance database
        database.log_call(
            call_id=callback_call_id,
            client_id=self.client_id,
            phone=self.client["phone"],
            call_type="CALLBACK_CONFIRM",
            recording_url=recording_url,
            transcript=f"AI: {full_callback_script}"
        )
        
        return full_callback_script
