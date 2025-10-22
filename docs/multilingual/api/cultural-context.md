# Cultural Context API

## 🌍 **Cultural Context API Documentation**

This document outlines the Cultural Context API for the Policy as Code platform, enabling cultural context awareness for Nordic-Baltic countries.

## 🎯 **Overview**

The Cultural Context API provides comprehensive cultural context services for:

- **Cultural Context Detection**: Automatic cultural context detection
- **Cultural Adaptation**: Cultural adaptation of AI responses
- **Cultural Sensitivity**: Cultural sensitivity validation
- **Cross-Cultural Communication**: Cross-cultural communication support

## 🔧 **API Endpoints**

### **Cultural Context Detection**

#### **POST /api/v1/detect-cultural-context**
Detect the cultural context of input text or communication.

**Request Body:**
```json
{
  "text": "Hei, miten voit?",
  "language": "fi",
  "context": "citizen_service",
  "user_profile": {
    "country": "FI",
    "region": "Helsinki",
    "language_preference": "fi"
  }
}
```

**Response:**
```json
{
  "detected_context": {
    "country": "FI",
    "region": "Helsinki",
    "cultural_values": ["equality", "transparency", "trust"],
    "social_norms": ["direct_communication", "privacy_respect"],
    "communication_style": "formal",
    "cultural_sensitivity": "high"
  },
  "confidence": 0.92,
  "recommendations": {
    "communication_tone": "respectful",
    "formality_level": "formal",
    "cultural_considerations": ["privacy", "equality"]
  }
}
```

### **Cultural Adaptation**

#### **POST /api/v1/adapt-cultural-context**
Adapt AI responses to cultural context.

**Request Body:**
```json
{
  "response_text": "Your application has been approved",
  "source_context": {
    "country": "US",
    "cultural_values": ["individualism", "efficiency"]
  },
  "target_context": {
    "country": "FI",
    "cultural_values": ["equality", "transparency", "trust"]
  },
  "communication_purpose": "citizen_notification"
}
```

**Response:**
```json
{
  "adapted_response": "Hakemuksenne on hyväksytty. Kiitos hakemuksestanne.",
  "cultural_adaptations": [
    {
      "type": "formality",
      "change": "increased_formality",
      "reason": "Finnish preference for formal communication"
    },
    {
      "type": "gratitude",
      "change": "added_gratitude",
      "reason": "Finnish cultural value of politeness"
    }
  ],
  "confidence": 0.88
}
```

### **Cultural Sensitivity Validation**

#### **POST /api/v1/validate-cultural-sensitivity**
Validate cultural sensitivity of AI responses.

**Request Body:**
```json
{
  "response_text": "Your application has been approved",
  "target_context": {
    "country": "SE",
    "cultural_values": ["equality", "lagom", "transparency"],
    "social_norms": ["consensus_building", "gender_equality"]
  },
  "sensitivity_requirements": ["gender_neutral", "inclusive_language"]
}
```

**Response:**
```json
{
  "is_culturally_sensitive": true,
  "sensitivity_score": 0.95,
  "validation_results": [
    {
      "requirement": "gender_neutral",
      "passed": true,
      "score": 1.0
    },
    {
      "requirement": "inclusive_language",
      "passed": true,
      "score": 0.9
    }
  ],
  "recommendations": []
}
```

## 🌍 **Supported Cultural Contexts**

### **Nordic Countries**
- **Finland (FI)**: Finnish cultural context
- **Sweden (SE)**: Swedish cultural context
- **Norway (NO)**: Norwegian cultural context
- **Denmark (DK)**: Danish cultural context
- **Iceland (IS)**: Icelandic cultural context

### **Baltic Countries**
- **Estonia (EE)**: Estonian cultural context
- **Latvia (LV)**: Latvian cultural context
- **Lithuania (LT)**: Lithuanian cultural context

### **Other Countries**
- **United States (US)**: US cultural context
- **Germany (DE)**: German cultural context
- **France (FR)**: French cultural context

## 🎯 **Cultural Values**

### **Nordic Values**
- **Equality**: Strong emphasis on social equality
- **Transparency**: High government transparency
- **Trust**: High trust in institutions
- **Sustainability**: Environmental consciousness
- **Innovation**: Embracing technology

### **Social Norms**
- **Direct Communication**: Direct and honest communication
- **Non-Confrontational**: Avoiding unnecessary conflict
- **Inclusive Communication**: Inclusive and respectful language
- **Privacy Respect**: Strong privacy protection

### **Communication Styles**
- **Formal Communication**: Appropriate formality levels
- **Respectful Tone**: Respectful and considerate language
- **Cultural Sensitivity**: Awareness of cultural differences
- **Accessibility**: Accessible communication

## 🔧 **Cultural Features**

### **Context Awareness**
- **Cultural Values**: Cultural value recognition
- **Social Norms**: Social norm awareness
- **Communication Patterns**: Communication pattern recognition
- **Regional Variations**: Regional cultural variations

### **Adaptation**
- **Cultural Adaptation**: Cultural response adaptation
- **Sensitivity Validation**: Cultural sensitivity validation
- **Cross-Cultural Communication**: Cross-cultural communication support
- **Bias Detection**: Cultural bias detection

### **Performance**
- **Fast Detection**: Fast cultural context detection
- **Batch Processing**: Efficient batch processing
- **Caching**: Cultural context caching
- **Scalability**: Scalable cultural services

## 🚀 **Implementation Status**

### **Current Status**
- **✅ Basic Cultural Awareness**: Basic cultural context detection
- **✅ Nordic Contexts**: Nordic cultural context support
- **✅ Adaptation**: Basic cultural adaptation
- **⚠️ Advanced Features**: Advanced cultural features in development

### **Planned Features**
- **Advanced Adaptation**: Enhanced cultural adaptation
- **Real-time Detection**: Real-time cultural context detection
- **Cultural Bias Detection**: Cultural bias detection and mitigation
- **Cross-Cultural Training**: Cross-cultural training support

## 📖 **Usage Examples**

### **Python SDK**
```python
from policy_as_code.cultural_context import CulturalContextClient

client = CulturalContextClient()

# Detect cultural context
result = client.detect_cultural_context(
    text="Hei, miten voit?",
    language="fi",
    context="citizen_service"
)

print(result.detected_context.country)  # "FI"
print(result.detected_context.cultural_values)  # ["equality", "transparency", "trust"]
```

### **REST API**
```bash
curl -X POST "http://localhost:8000/api/v1/detect-cultural-context" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Velkommen til vores service",
    "language": "da",
    "context": "citizen_service"
  }'
```

## 📚 **Resources**

- **Cultural Context Models**: [Cultural Context Models](https://huggingface.co/models?pipeline_tag=text-classification&search=cultural+context)
- **Nordic Cultural Research**: [Nordic Cultural Research](https://www.nordicculturalresearch.org/)
- **Cultural Sensitivity**: [Cultural Sensitivity](https://www.culturalsensitivity.org/)
- **Cross-Cultural Communication**: [Cross-Cultural Communication](https://www.crossculturalcommunication.org/)

## 🔗 **Related Documentation**

- **Multilingual Support**: [Multilingual Guide](../nordic-languages.md)
- **Translation API**: [Translation API](translation.md)
- **Language Detection**: [Language Detection API](language-detection.md)
- **Cross-Language**: [Cross-Language API](cross-language.md)

---

**Status**: Basic Implementation Complete ✅ | Advanced Features in Development 🚧
