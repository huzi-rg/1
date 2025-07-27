using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using Newtonsoft.Json;
using UnityEngine.UI;
using UnityEngine.Events;

public class DeepSeekAPI : MonoBehaviour
{
    private string apiKey = "sk-2981d36194124eb6ac091479288df8d8";
    private string apiUrl = "https://api.deepseek.com/v1/chat/completions";

    
  
    public  void SendMessageToDeepSeek(string message,UnityAction<string> callback)
    {
        StartCoroutine(PostRequest(message, callback));
    }

     IEnumerator PostRequest(string message, UnityAction<string> callback)
    {
        // 创建请求体
        var requestBody = new
        {
            model = "deepseek-chat",
            messages = new[]
            {
                new { role = "user", content = message }
            }
        };

        // 使用Newtonsoft.Json序列化
        string jsonBody = JsonConvert.SerializeObject(requestBody);

        // 创建UnityWebRequest
        UnityWebRequest request = new UnityWebRequest(apiUrl, "POST");
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        request.SetRequestHeader("Authorization", "Bearer " + apiKey);

        // 发送请求
        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError("Error: " + request.error);
            Debug.LogError("Response: " + request.downloadHandler.text); // 打印详细错误信息
        }
        else
        {
            // 处理响应
            string responseJson = request.downloadHandler.text;
            Debug.Log("Response: " + responseJson);
            

            // 解析响应
            var response = JsonConvert.DeserializeObject<DeepSeekResponse>(responseJson);
            if (response != null && response.choices.Length > 0)
            {
                string reply = response.choices[0].message.content;
                Debug.Log("DeepSeek says: " + reply);
                callback(reply);
            }
            else
            {
                Debug.LogError("Failed to parse response.");
            }
        }
    }

    // 定义响应数据结构
    [System.Serializable]
    private class DeepSeekResponse
    {
        public Choice[] choices;
    }

    [System.Serializable]
    private class Choice
    {
        public Message message;
    }

    [System.Serializable]
    private class Message
    {
        public string role;
        public string content;
    }
}