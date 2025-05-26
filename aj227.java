package com.libaolu.jmeter;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.libaolu.util.BaoluUtil;
import com.libaolu.util.DateUtil;
import com.libaolu.util.a;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.UnsupportedEncodingException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.regex.Pattern;

public class AggregateGraphReport {
   private Map<String, List<Long>> a = new HashMap();
   private Map<String, List<Long>> b = new HashMap();
   private Integer c;
   private Integer d;
   // $FF: synthetic field
   private static boolean $assertionsDisabled = !AggregateGraphReport.class.desiredAssertionStatus();

   public static void main(String[] args) {
      AggregateGraphReport agr;
      AggregateGraphReport var54 = agr = new AggregateGraphReport();

      try {
         InputStream var55 = var54.getClass().getClassLoader().getResourceAsStream("banner/banner.txt");
         Throwable var56 = null;
         boolean var102 = false;

         try {
            var102 = true;
            if (var55 == null) {
               var102 = false;
            } else {
               label1656: {
                  while(true) {
                     boolean var119 = false;

                     try {
                        var119 = true;
                        int var57;
                        if ((var57 = var55.read()) != -1) {
                           System.out.write(var57);
                           continue;
                        }

                        var119 = false;
                        break;
                     } catch (IOException var131) {
                        var119 = false;
                     } finally {
                        if (var119) {
                           try {
                              var55.close();
                           } catch (IOException var126) {
                              var126.printStackTrace();
                           }

                        }
                     }

                     try {
                        var55.close();
                        var102 = false;
                     } catch (IOException var127) {
                        var127.printStackTrace();
                        var102 = false;
                     }
                     break label1656;
                  }

                  try {
                     var55.close();
                     var102 = false;
                  } catch (IOException var128) {
                     var128.printStackTrace();
                     var102 = false;
                  }
               }
            }
         } catch (Throwable var133) {
            var56 = var133;
            throw var133;
         } finally {
            if (var102) {
               if (var55 != null) {
                  if (var56 != null) {
                     try {
                        var55.close();
                     } catch (Throwable var125) {
                        var56.addSuppressed(var125);
                     }
                  } else {
                     var55.close();
                  }
               }

            }
         }

         if (var55 != null) {
            var55.close();
         }
      } catch (IOException var135) {
         var135.printStackTrace();
      }

      if (args.length == 0) {
         System.out.println("Parameter error! Check the number of parameters please.");
         System.exit(0);
      }

      try {
         System.out.println("============================START====================================");
      } catch (Exception var124) {
         var124.printStackTrace();
         System.out.println("=============================END=====================================");
         System.exit(0);
      }

      File jtlFile = new File(args[0]);
      byte var157 = 0;
      if (args.length != 2 && args.length != 3) {
         System.out.println("Parameter error! Check the number of parameters please.");
         var157 = 1;
      } else {
         if (!jtlFile.exists()) {
            System.out.println("Parameter error! The current JTL file [" + args[0] + "] does not exist.");
            var157 = 2;
         }

         String var58 = args[1];
         if (!Pattern.compile("^[-\\+]?[\\d]*$").matcher(var58).matches()) {
            System.out.println("Parameter error! The interval parameter must be Integer.");
            var157 = 3;
         }

         if (Integer.parseInt(args[1]) <= 0 || Integer.parseInt(args[1]) > 99999) {
            System.out.println("Parameter error! The interval parameter parameter is not valid.");
            var157 = 4;
         }
      }

      if (var157 != 0) {
         System.exit(0);
      }

      long t1 = System.currentTimeMillis();
      int intervalTime = Integer.parseInt(args[1]);
      new SimpleDateFormat("HH:mm:ss");
      SimpleDateFormat sFormat2 = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
      SimpleDateFormat sFormat3 = new SimpleDateFormat("HHmmss");
      String graphFilePath;
      if (args.length == 3) {
         if (!args[2].endsWith("/")) {
            graphFilePath = args[2] + "/AggregateGraphReport" + sFormat3.format(t1);
         } else {
            graphFilePath = args[2] + "AggregateGraphReport" + sFormat3.format(t1);
         }
      } else {
         graphFilePath = "AggregateGraphReport" + sFormat3.format(t1);
      }

      String dataPath = graphFilePath + File.separator + "data" + File.separator;
      File var159;
      (var159 = new File(graphFilePath)).mkdirs();
      File var60;
      File var158;
      if (args.length == 2) {
         (var158 = new File(var159.getName() + File.separator + "css")).mkdir();
         (new File(var159.getName() + File.separator + "data")).mkdir();
         (var60 = new File(var159.getName() + File.separator + "js")).mkdir();
      } else {
         (var158 = new File(var159.getAbsoluteFile() + File.separator + "css")).mkdir();
         (new File(var159.getAbsoluteFile() + File.separator + "data")).mkdir();
         (var60 = new File(var159.getAbsoluteFile() + File.separator + "js")).mkdir();
      }

      InputStream var61 = agr.getClass().getClassLoader().getResourceAsStream("css/bootstrap.min.css");
      InputStream var62 = agr.getClass().getClassLoader().getResourceAsStream("js/bootstrap.min.js");
      InputStream var63 = agr.getClass().getClassLoader().getResourceAsStream("js/highstock.js");
      InputStream var64 = agr.getClass().getClassLoader().getResourceAsStream("js/jquery.min.js");
      InputStream var65 = agr.getClass().getClassLoader().getResourceAsStream("js/perf-chars.js");
      InputStream var66 = agr.getClass().getClassLoader().getResourceAsStream("js/exporting.js");
      InputStream var67 = agr.getClass().getClassLoader().getResourceAsStream("js/offline-exporting.js");
      InputStream var68 = agr.getClass().getClassLoader().getResourceAsStream("index.html");
      com.libaolu.util.a.a(var61, new File(var158.getAbsoluteFile() + File.separator + "bootstrap.min.css"));
      com.libaolu.util.a.a(var62, new File(var60.getAbsoluteFile() + File.separator + "bootstrap.min.js"));
      com.libaolu.util.a.a(var63, new File(var60.getAbsoluteFile() + File.separator + "highstock.js"));
      com.libaolu.util.a.a(var64, new File(var60.getAbsoluteFile() + File.separator + "jquery.min.js"));
      com.libaolu.util.a.a(var65, new File(var60.getAbsoluteFile() + File.separator + "perf-chars.js"));
      com.libaolu.util.a.a(var66, new File(var60.getAbsoluteFile() + File.separator + "exporting.js"));
      com.libaolu.util.a.a(var67, new File(var60.getAbsoluteFile() + File.separator + "offline-exporting.js"));
      com.libaolu.util.a.a(var68, new File(var159.getAbsoluteFile() + File.separator + "index.html"));
      System.out.println(DateUtil.getCurrentDate() + " - " + graphFilePath + " - 报告目录已创建");
      BufferedReader reader = null;
      BufferedWriter infoWriter = null;
      BufferedWriter realTimeWriter = null;
      BufferedWriter finalResultWriter = null;
      BufferedWriter vuserResultWriter = null;
      BufferedWriter bytesResultWriter = null;

      try {
         reader = new BufferedReader(new InputStreamReader(new FileInputStream(jtlFile), StandardCharsets.UTF_8));
         realTimeWriter = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(dataPath + "real-time.js"), StandardCharsets.UTF_8));
         finalResultWriter = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(dataPath + "final-result.js"), StandardCharsets.UTF_8));
         infoWriter = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(dataPath + "info.js"), StandardCharsets.UTF_8));
         vuserResultWriter = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(dataPath + "vuser-result.js"), StandardCharsets.UTF_8));
         bytesResultWriter = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(dataPath + "bytes-result.js"), StandardCharsets.UTF_8));
      } catch (FileNotFoundException var123) {
         var123.printStackTrace();
      }

      Map<String, Map<String, Integer>> samplerMap = new HashMap();
      Map<String, Map<String, Integer>> threadGroupMap = new HashMap();
      Map<String, List<Integer>> bytesThroughputMap = new HashMap();
      Map<String, Map<String, Long>> finalEachSamplerData = new HashMap();
      Map<String, List<Integer>> finalEachSamplerRtMap = new HashMap();
      Map<String, Long> lastSendStampMap = new HashMap();
      long rowNum = 0L;
      boolean var85 = false;

      label1591: {
         try {
            var85 = true;
            if (reader.readLine().startsWith("<?xml")) {
               System.out.println("XML is not supported. Only CSV is currently supported.");
               System.exit(0);
            }

            Long startTime = 0L;
            Long endTime = 0L;
            Long lastCalcTime = 0L;
            realTimeWriter.write("var realTimeData=[");

            while(true) {
               String line;
               String grpThreads;
               while((line = reader.readLine()) != null) {
                  if (line.indexOf(", number of failing samples") > 0) {
                     line = line.replace(", number of failing samples", "number of failing samples");
                  }

                  String[] data;
                  if ((data = line.split(",")).length >= 13) {
                     Long currentTime = 0L;
                     if (data[0].length() != 13) {
                        if (data[0].length() == 23) {
                           currentTime = DateUtil.a(data[0], "yyyy/MM/dd HH:mm:ss.SSS");
                        } else if (data[0].length() == 19) {
                           currentTime = DateUtil.a(data[0], "yyyy/MM/dd HH:mm:ss");
                        }
                     } else {
                        currentTime = Long.parseLong(data[0]);
                     }

                     String samplerName = data[2];
                     String threadGroupMsg = data[5];
                     String isSuccess = data[7];
                     String receiveBytes = data[9];
                     String sendBytes = data[10];
                     grpThreads = data[11];
                     Integer rt = Integer.parseInt(data[1]);
                     if (rowNum == 0L) {
                        startTime = currentTime;
                        lastCalcTime = currentTime;
                        lastSendStampMap.put("lastSendStamp", currentTime);
                     }

                     endTime = currentTime + (long)rt;
                     Map tempEachSamplerData;
                     HashMap tempEachSamplerData1;
                     if (currentTime - lastCalcTime < (long)(intervalTime * 1000)) {
                        if ((tempEachSamplerData = (Map)samplerMap.get(samplerName)) != null) {
                           tempEachSamplerData.put("avgRt", (Integer)tempEachSamplerData.get("avgRt") + rt);
                           if ("true".equals(isSuccess)) {
                              tempEachSamplerData.put("successCnt", (Integer)tempEachSamplerData.get("successCnt") + 1);
                              tempEachSamplerData.putIfAbsent("failCnt", 0);
                           } else {
                              tempEachSamplerData.put("failCnt", (Integer)tempEachSamplerData.get("failCnt") + 1);
                           }
                        } else {
                           (tempEachSamplerData = new HashMap()).put("avgRt", rt);
                           if ("true".equals(isSuccess)) {
                              tempEachSamplerData.put("successCnt", 1);
                              tempEachSamplerData.put("failCnt", 0);
                           } else {
                              tempEachSamplerData.put("successCnt", 0);
                              tempEachSamplerData.put("failCnt", 1);
                           }

                           samplerMap.put(samplerName, tempEachSamplerData);
                        }

                        String threadGroupName = BaoluUtil.b(threadGroupMsg);
                        Object groupThreadIndex;
                        if ((groupThreadIndex = (Map)threadGroupMap.get(threadGroupName)) == null) {
                           groupThreadIndex = new HashMap();
                        }

                        ((Map)groupThreadIndex).put(grpThreads, 1);
                        String map11 = JSONObject.toJSONString(groupThreadIndex);
                        Map map1 = JSONObject.parseObject(map11 , Map.class);
                        threadGroupMap.put(threadGroupName, map1);
                        List<Integer> receiveBytesList = (List)bytesThroughputMap.get("Receive Bytes per Second");
                        List<Integer> sendBytesList = (List)bytesThroughputMap.get("Send Bytes per Second");

                        if (receiveBytesList == null) {
                           receiveBytesList = new ArrayList<>();
                           bytesThroughputMap.put("Receive Bytes per Second", receiveBytesList);
                        }

                        if (sendBytesList == null) {
                           sendBytesList = new ArrayList<>();
                           bytesThroughputMap.put("Send Bytes per Second", sendBytesList);
                        }

                        // 处理 receiveBytes 和 sendBytes 的空字符串情况
                        try {
                           if (receiveBytes != null && !receiveBytes.isEmpty()) {
                              receiveBytesList.add(Integer.valueOf(receiveBytes));
                           } else {
                              receiveBytesList.add(0); // 或者你可以选择添加其他默认值
                           }
                        } catch (NumberFormatException e) {
                           System.out.println("Invalid receiveBytes value: " + receiveBytes + " at row " + rowNum);
                           receiveBytesList.add(0); // 或者你可以选择添加其他默认值
                        }

                        try {
                           if (sendBytes != null && !sendBytes.isEmpty()) {
                              sendBytesList.add(Integer.valueOf(sendBytes));
                           } else {
                              sendBytesList.add(0); // 或者你可以选择添加其他默认值
                           }
                        } catch (NumberFormatException e) {
                           System.out.println("Invalid sendBytes value: " + sendBytes + " at row " + rowNum);
                           sendBytesList.add(0); // 或者你可以选择添加其他默认值
                        }

                        bytesThroughputMap.put("Receive Bytes per Second", receiveBytesList);
                        bytesThroughputMap.put("Send Bytes per Second", sendBytesList);
                     } else if (currentTime - lastCalcTime >= (long)(intervalTime * 1000)) {
                        GraphData graphData = new GraphData(); // Ensure GraphData is properly initialized
                        graphData.setTime(sFormat2.format(currentTime));

                        Map<String, Integer> successTpsMap = new HashMap<>();
                        Map<String, Integer> failTpsMap = new HashMap<>();
                        Map<String, Integer> rtMap = new HashMap<>();
                        Map<String, Integer> groupMaxActiveThread = new HashMap<>();
                        Map<String, Integer> receiveSendBytesMap = new HashMap<>();

                        Long lastSendTimeMs = currentTime - (Long)lastSendStampMap.get("lastSendStamp");
                        Iterator<Entry<String, Map<String, Integer>>> var46 = samplerMap.entrySet().iterator();

                        while (var46.hasNext()) {
                           Entry<String, Map<String, Integer>> entry = var46.next();
                           Map<String, Integer> samplerData = entry.getValue();

                           samplerData.putIfAbsent("failCnt", 0);
                           Integer successTps = (samplerData.get("successCnt") == null ? 0 : samplerData.get("successCnt")) * 1000 / lastSendTimeMs.intValue();
                           Integer failTps = (samplerData.get("failCnt") == null ? 0 : samplerData.get("failCnt")) * 1000 / lastSendTimeMs.intValue();
                           // 避免除以零的错误
                           Integer avgRt = (samplerData.get("successCnt") + samplerData.get("failCnt")) != 0
                                   ? (samplerData.get("avgRt") == null ? 0 : samplerData.get("avgRt")) / (samplerData.get("successCnt") + samplerData.get("failCnt"))
                                   : 0; // 设置默认值为 0

                           successTpsMap.put(entry.getKey(), successTps);
                           failTpsMap.put(entry.getKey(), failTps);
                           rtMap.put(entry.getKey(), avgRt);

                           samplerData.put("successCnt", 0);
                           samplerData.put("failCnt", 0);
                           samplerData.put("avgRt", 0);
                        }

                        String threadGroupName = BaoluUtil.b(threadGroupMsg);
                        groupMaxActiveThread.put(threadGroupName, Integer.valueOf(grpThreads));

                        Iterator<Entry<String, List<Integer>>> var153 = bytesThroughputMap.entrySet().iterator();

                        while (var153.hasNext()) {
                           Entry<String, List<Integer>> entry1 = var153.next();
                           int totalBytes = 0;

                           for (Integer bytes : entry1.getValue()) {
                              totalBytes += bytes;
                           }

                           receiveSendBytesMap.put(entry1.getKey(), totalBytes / lastSendTimeMs.intValue() * 1000 / 1024);
                           entry1.getValue().clear();
                        }

                        graphData.setSuccTps(successTpsMap);
                        graphData.setFailTps(failTpsMap);
                        graphData.setRt(rtMap);
                        graphData.setVuser(groupMaxActiveThread);
                        graphData.setRsBytes(receiveSendBytesMap);

                        realTimeWriter.write(JSON.toJSONString(graphData) + ",");
                        realTimeWriter.newLine();
                        realTimeWriter.flush();

                        lastCalcTime = currentTime + (long)rt;
                        lastSendStampMap.put("lastSendStamp", currentTime);
                     }

                     tempEachSamplerData = (Map)finalEachSamplerData.get(samplerName);
                     List<Integer> tempEachSamplerRtList = (List)finalEachSamplerRtMap.get(samplerName);
                     if (tempEachSamplerData != null) {
                        tempEachSamplerData.put("rts", (Long)tempEachSamplerData.get("rts") + (long)rt);
                        // 修改点：无论成功/失败，都记录响应时间
                        ((List)tempEachSamplerRtList).add(rt);
                        if ("true".equals(isSuccess)) {
                           tempEachSamplerData.put("successCnt", (Long)tempEachSamplerData.get("successCnt") + 1L);
                        } else {
                           tempEachSamplerData.put("failCnt", (Long)tempEachSamplerData.get("failCnt") + 1L);
                        }
                     } else {
                        (tempEachSamplerData = new HashMap()).put("rts", rt.longValue());
                        (tempEachSamplerRtList = new ArrayList()).add(rt); // 记录所有事务的响应时间
                        if ("true".equals(isSuccess)) {
                           tempEachSamplerData.put("successCnt", 1L);
                           tempEachSamplerData.put("failCnt", 0L);
                        } else {
                           tempEachSamplerData.put("successCnt", 0L);
                           tempEachSamplerData.put("failCnt", 1L);
                        }

                        finalEachSamplerData.put(samplerName, tempEachSamplerData);
                        finalEachSamplerRtMap.put(samplerName, tempEachSamplerRtList);
                     }

                     if (agr.a.get(samplerName) != null) {
                        ((List)agr.a.get(samplerName)).add(currentTime);
                     } else {
                        ArrayList eachSamplerSendStamp;
                        (eachSamplerSendStamp = new ArrayList()).add(currentTime);
                        agr.a.put(samplerName, eachSamplerSendStamp);
                     }

                     if (agr.b.get(samplerName) != null) {
                        ((List)agr.b.get(samplerName)).add(endTime);
                     } else {
                        ArrayList eachSamplerEndStamp;
                        (eachSamplerEndStamp = new ArrayList()).add(endTime);
                        agr.b.put(samplerName, eachSamplerEndStamp);
                     }

                     ++rowNum;
                  } else {
                     System.out.println("JTL file is in a non-standard format, please check " + rowNum + " line");
                     System.exit(0);
                  }
               }

               realTimeWriter.write("{}]");
               realTimeWriter.flush();
               vuserResultWriter.write("var vuserResult=" + JSON.toJSONString(threadGroupMap));
               vuserResultWriter.flush();
               Iterator var138 = bytesThroughputMap.entrySet().iterator();

               while(var138.hasNext()) {
                  ((Entry)var138.next()).setValue(new ArrayList());
               }

               bytesResultWriter.write("var byteResult=" + JSON.toJSONString(bytesThroughputMap));
               bytesResultWriter.flush();
               System.out.println(DateUtil.getCurrentDate() + " - " + graphFilePath + " - 图表数据已生成");
               var138 = finalEachSamplerData.entrySet().iterator();

               while(var138.hasNext()) {
                  Entry entry;
                  Map<String, Object> innerMap = (Map)(entry = (Entry)var138.next()).getValue();
                  Collections.sort((List)agr.a.get(entry.getKey()));
                  Collections.sort((List)agr.b.get(entry.getKey()));
                  int Max = ((List)agr.b.get(entry.getKey())).size() - 1;
                  Long howLongRunning;
                  Double tps;
                  if ((howLongRunning = (Long)((List)agr.b.get(entry.getKey())).get(Max) - (Long)((List)agr.a.get(entry.getKey())).get(0)).intValue() == 0) {
                     tps = 0.0D;
                  } else {
                     tps = ((Long)innerMap.get("successCnt")).doubleValue() / (double)howLongRunning.intValue() * 1000.0D;
                  }

                  innerMap.put("tps", (new BigDecimal(tps)).setScale(3, RoundingMode.HALF_UP).doubleValue());
                  innerMap.put("rt", (Long)innerMap.get("rts") / ((Long)innerMap.get("successCnt") + (Long)innerMap.get("failCnt")));
                  innerMap.put("actualDurationTime", howLongRunning);
                  if ((grpThreads = agr.a((List)finalEachSamplerRtMap.get(entry.getKey()))) != null) {
                     String[] times = grpThreads.split(",");
                     innerMap.put("tp90", Long.parseLong(times[0]));
                     innerMap.put("tp95", Long.parseLong(times[1]));
                     innerMap.put("tp99", Long.parseLong(times[2]));
                  }

                  innerMap.put("Min", agr.c);
                  innerMap.put("Max", agr.d);
                  innerMap.remove("startTime");
                  innerMap.remove("endTime");
               }

               finalResultWriter.write("var finalResult=" + JSON.toJSONString(finalEachSamplerData));
               finalResultWriter.flush();
               HashMap infoMap;
               (infoMap = new HashMap()).put("fileName", args[0]);
               infoMap.put("startTime", sFormat2.format(startTime));
               infoMap.put("endTime", sFormat2.format(endTime));
               infoWriter.write("var info=" + JSON.toJSONString(infoMap));
               infoWriter.flush();
               long t2 = System.currentTimeMillis();
               System.out.println(DateUtil.getCurrentDate() + " - 结果统计已完成，总耗时：" + DateUtil.a(t1, t2));
               System.out.println("=============================END=====================================");
               var85 = false;
               break label1591;
            }
         } catch (Exception var129) {
            var129.printStackTrace();
            System.out.println("JTL file parsing encountered an exception, please check line " + rowNum + " of the file.");
            var85 = false;
         } finally {
            if (var85) {
               try {
                  if (reader != null) {
                     reader.close();
                  }

                  if (finalResultWriter != null) {
                     finalResultWriter.close();
                  }

                  if (realTimeWriter != null) {
                     realTimeWriter.close();
                  }

                  if (infoWriter != null) {
                     infoWriter.close();
                  }

                  if (vuserResultWriter != null) {
                     vuserResultWriter.close();
                  }

                  if (bytesResultWriter != null) {
                     bytesResultWriter.close();
                  }
               } catch (Exception var121) {
                  var121.printStackTrace();
               }

            }
         }

         try {
            if (reader != null) {
               reader.close();
            }

            if (finalResultWriter != null) {
               finalResultWriter.close();
            }

            if (realTimeWriter != null) {
               realTimeWriter.close();
            }

            if (infoWriter != null) {
               infoWriter.close();
            }

            if (vuserResultWriter != null) {
               vuserResultWriter.close();
            }

            if (bytesResultWriter != null) {
               bytesResultWriter.close();
            }

            return;
         } catch (Exception var120) {
            var120.printStackTrace();
            return;
         }
      }

      try {
         if (reader != null) {
            reader.close();
         }

         if (finalResultWriter != null) {
            finalResultWriter.close();
         }

         if (realTimeWriter != null) {
            realTimeWriter.close();
         }

         if (infoWriter != null) {
            infoWriter.close();
         }

         if (vuserResultWriter != null) {
            vuserResultWriter.close();
         }

         if (bytesResultWriter != null) {
            bytesResultWriter.close();
         }

      } catch (Exception var122) {
         var122.printStackTrace();
      }
   }

   public void setPerSamplerMinTime(File jtlFile) {
      BufferedReader reader = null;
      try {
         reader = new BufferedReader(new InputStreamReader(new FileInputStream(jtlFile), "UTF-8"));
      } catch (FileNotFoundException | UnsupportedEncodingException var22) {
         var22.printStackTrace();
      }

      try {
         if (!$assertionsDisabled && reader == null) {
            throw new AssertionError();
         }

         if (reader.readLine().startsWith("<?xml")) {
            System.out.println("XML is not supported. Only CSV is currently supported.");
            System.exit(0);
         }
      } catch (IOException var21) {
         var21.printStackTrace();
      }

      while(true) {
         boolean var17 = false;

         try {
            var17 = true;
            String line;
            if ((line = reader.readLine()) != null) {
               String[] data;
               if ((data = line.split(",")).length == 16) {
                  if (this.a.get(data[2]) != null) {
                     ((List)this.a.get(data[2])).add(Long.parseLong(data[0]));
                  } else {
                     ArrayList rtList;
                     (rtList = new ArrayList()).add(Long.parseLong(data[0]));
                     this.a.put(data[2], rtList);
                  }
               } else {
                  System.out.println("JTL file exception, check it please.");
                  System.exit(0);
               }
               continue;
            }

            Iterator var6 = this.a.entrySet().iterator();

            while(var6.hasNext()) {
               Entry<String, List<Long>> entry = (Entry)var6.next();
               Collections.sort((List)this.a.get(entry.getKey()));
            }

            var17 = false;
            break;
         } catch (IOException | NumberFormatException var23) {
            var23.printStackTrace();
            var17 = false;
         } finally {
            if (var17) {
               try {
                  reader.close();
               } catch (IOException var18) {
                  var18.printStackTrace();
               }

            }
         }

         try {
            reader.close();
            return;
         } catch (IOException var19) {
            var19.printStackTrace();
            return;
         }
      }

      try {
         reader.close();
      } catch (IOException var20) {
         var20.printStackTrace();
      }
   }

   private String a(List<Integer> list) {
      if (list.size() == 0) {
         return "0,0,0";
      } else {
         Collections.sort(list);
         this.c = (Integer)list.get(0);
         this.d = (Integer)list.get(list.size() - 1);
         Float pct1Value = Float.parseFloat("90") / 100.0F;
         Float pct2Value = Float.parseFloat("95") / 100.0F;
         Float pct3Value = Float.parseFloat("99") / 100.0F;
         HashMap valuesMap;
         if ((valuesMap = new HashMap()).isEmpty()) {
            valuesMap.put((double)pct1Value, 0);
            valuesMap.put((double)pct2Value, 0);
            valuesMap.put((double)pct3Value, 0);
         }
         Iterator var6 = valuesMap.entrySet().iterator();

         while(var6.hasNext()) {
            Entry<Double, Integer> val = (Entry)var6.next();
            long target = Math.round((double)list.size() * (Double)val.getKey());

            for(int i = 0; i < list.size(); ++i) {
               if (--target == 0L) {
                  valuesMap.put(val.getKey(), list.get(i));
               }
            }
         }

         return valuesMap.get((double)pct1Value) + "," + valuesMap.get((double)pct2Value) + "," + valuesMap.get((double)pct3Value);
      }
   }

   public String getLicenseKey() {
      InputStream in = this.getClass().getClassLoader().getResourceAsStream("raw/libaolu.lic");
      BufferedReader reader = new BufferedReader(new InputStreamReader(in));
      String key = null;
      while(true) {
         boolean var13 = false;

         label78: {
            try {
               var13 = true;
               String line;
               if ((line = reader.readLine()) != null) {
                  key = line;
                  continue;
               }

               var13 = false;
            } catch (IOException var17) {
               var17.printStackTrace();
               var13 = false;
               break label78;
            } finally {
               if (var13) {
                  try {
                     reader.close();
                     in.close();
                  } catch (IOException var14) {
                     var14.printStackTrace();
                  }

               }
            }

            try {
               reader.close();
               in.close();
            } catch (IOException var16) {
               var16.printStackTrace();
            }
            break;
         }

         try {
            reader.close();
            in.close();
         } catch (IOException var15) {
            var15.printStackTrace();
         }
         break;
      }

      return key;
   }
}
